# Trial: FreeToken

[FlashML-org/FreeToken](https://github.com/FlashML-org/FreeToken) — a MoE serving engine
for machines with **too little** VRAM: hot experts on the card, the rest in host RAM, an
LRU cache between them. Apache-2.0, release `v0.1.2`, repository six weeks old at the time
of testing. Evaluated 2026-09-01 on
[cloudscale `GPU2-256-40-2-1600`](../README.md).

**This is not protocol `v1`.** Method is stated per measurement; nothing here is
comparable with the model directories.

## Why it was tried

Four models this week failed on VRAM alone — GLM-5.3-Flash NVFP4 at 90.7 GiB per card,
MiniMax-M3 at 116, Qwen3.5-397B at 117, against 95.6 available. FreeToken is built for
exactly that constraint, and the machine has 230 GB of host RAM sitting idle.

## Result in one sentence

On **one** card with 143 GB of experts in host RAM, DeepSeek-V4-Flash-0731 delivers
**37–39 tok/s** against 75.3 tok/s for SGLang on **two** cards — and the second card stays
free for another model, with no measurable interference between them.

## Measurements

DSv4-Flash-0731, 1000-token generation, three runs averaged, short prompt.

| Constellation | Card 0 | Card 1 |
|---|---|---|
| FreeToken alone, second card empty | **39.0 / 39.0 / 38.9 tok/s** | — |
| FreeToken, neighbour loaded but idle | 36.8 tok/s | — |
| FreeToken under the neighbour's load | **38.5 tok/s** | — |
| Neighbour alone (Qwen3.6-35B-A3B-FP8, vLLM) | — | 140.5 tok/s |
| Neighbour under FreeToken's load | — | 196.2 tok/s |

**No measurable mutual interference.** A model resident in VRAM barely touches PCIe while
decoding, so it does not compete with FreeToken's expert streaming. Contention would
require *both* sides to stream.

The neighbour measuring faster under load (196) than alone (140) is an artefact of the
measurement order — the first run hit a freshly loaded vLLM without warm CUDA graphs. Not
a finding.

## Bandwidth profile of this machine

`ft bench bw` measures the hardware ceilings and picks the MoE backend from them:

```
CPU STREAM read 170.3 GB/s  |  PCIe H2D 57.8  D2H 56.6 GB/s  |  40 cores

bf16    9.00 MB/expert   CPU-MoE 72.4  PCIe 53.7 GB/s   1.35x  -> hybrid available
nvfp4   7.61 MB          CPU-MoE 52.9  PCIe 53.6        0.99x  -> hybrid available
fp8     3.00 MB          CPU-MoE  n/a  PCIe 53.6          -    -> offload only
mxfp4  12.62 MB          CPU-MoE 18.8  PCIe 53.5        0.35x
```

**FP8 has no CPU compute path** — `CPU MoE has no fp8_block weight path; hybrid
unavailable`. DSv4-0731 is FP8 block-quantised and therefore runs in the less favourable
`offload` mode. An NVFP4 checkpoint would get `hybrid`, which the profile says computes
roughly half the misses on the CPU instead of fetching them over PCIe. Untested.

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| `--max-seq-len-override` | **must be set** | without a limit, one over-long prompt takes the backend worker down with a CUDA OOM, and the server does **not** restart it — it shuts itself down |
| `--kv-reserve-tokens` | ≥ 2× max-seq-len | default is 8192; `--moe-cache-auto` otherwise gives nearly all memory to experts |
| container `--init` | set it | otherwise a zombie PID survives and `docker rm -f` fails with `PID ... is zombie and can not be killed` |
| GPU selection | `CUDA_VISIBLE_DEVICES` | the documented `--gpu N` does not exist in 0.1.2 |

### The OOM crash, and how to contain it

No limit, 262,144 tokens of KV reserved, one 215k-token prompt:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.14 GiB.
GPU 0 has a total capacity of 94.97 GiB of which 1023.56 MiB is free
Backend supervisor: backend worker freetoken-TP0-scheduler exited
Backend worker is gone and cannot be restarted; stopping the API server
```

The KV cache was large enough — the OOM comes from **prefill working memory**.

Verified against `--max-seq-len-override 32768` with `--kv-reserve-tokens 65536`:

```
  2,458 tokens   OK        9.4s
 59,909 tokens   HTTP 400  0.1s
148,432 tokens   HTTP 400  0.2s
529,963 tokens   HTTP 400  0.8s
  2,452 tokens   OK        4.2s   <- server alive
```

Rejection happens **at the API in under a second**, before prefill memory is requested. A
prompt two and a half times larger than the fatal one is refused cleanly. The failure is
containable.

## Two values that cannot be trusted

**`/v1/models` returns 200 before the model is ready.** Requests then get 503 until the
experts finish loading. The reliable signal is the log line `API server is ready to
serve`. A health check on `/v1/models` sends traffic into a void — it caught us twice.

**`max_model_len` reports 1,048,576** where 64,000 or 262,144 were actually usable,
depending on configuration. Passing the reported number to a gateway produces
`context_length_exceeded` mid-session.

## What is actually supported

The docs list more than the release implements. Contents of `freetoken/models/` in 0.1.2:

```
deepseek_v4  gemma4  gguf  glm4_moe  glm_moe_dsa  gpt_oss  llama
minimax_m2   minimax_m3  mistral  muse_glimmer  qwen2  qwen3  qwen3_5_moe  qwen3_moe
```

- **GLM-5.3-Flash is absent** (`glm5_next`) — `glm_moe_dsa` is GLM-5.2, `glm4_moe` is 4.7
- **Qwen3.8-Flash-Next is absent** (`qwen4_exp`), although `docs/models.md` lists it
- **`minimax_m3` is present** — the 233 GiB model that did not fit at 116 GB per card
  would be reachable this way

Same pattern as the `--gpu` flag: the repository docs describe a newer state than the
published release.

## Installation

Not on the host — the build needs `CUDA_HOME`, and the VM carries only the driver:

```
RuntimeError: CUDA_HOME is required to build freetoken.kernel._pinned_tensor
             because it links against the CUDA runtime API.
```

The host also runs Python 3.14 where the devel image brings 3.12. Hence a container build
against `nvidia/cuda:13.0.1-devel-ubuntu24.04`; roughly twenty minutes, 22.3 GB image.
`numpy` must be installed **before** FreeToken or the build script fails importing torch.

## Verdict

**Out for production serving.** SGLang delivers twice the throughput on the same hardware,
with 256 concurrent requests against `max_running_req=4`, and without the operational
traps above.

**Viable as a second model on the otherwise idle card** — for chat with short prompts,
behind a hard context limit. The economic point is that a machine which could previously
run one model runs two, at 38 and 140+ tok/s, without interference.

The sensible split is the opposite of the obvious one: **the large model on FreeToken for
chat**, and a fast, full-context model on the free card for agent work. Not the other way
round — 32k of context is not enough for agentic use.

## Not planned

- **FreeToken as a replacement for SGLang.** Half the speed, a quarter of the concurrency,
  one GPU.
- **MiniMax-M3 through FreeToken.** Technically the only route to that model on this
  machine, but 226 GiB of download for a setup whose context has to be capped at 32k.

## Not measured

- **Where the OOM boundary actually is.** 32,768 runs, 215,000 killed it; the space
  between was not searched. Each attempt costs a six-minute restart.
- **`max_running_req=4`.** Not varied, no concurrency series.
- **`hybrid` on an NVFP4 checkpoint.** The profile promises the CPU path there; on FP8 it
  was unavailable.
