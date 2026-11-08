# cloudscale.ch `GPU2-512-80-4-800`

4× RTX PRO 6000 Blackwell Max-Q in a fully virtualised KVM guest. Everything below
was measured on this machine.

| | |
|---|---|
| Provider | cloudscale.ch, flavour `GPU2-512-80-4-800` |
| GPU | 4× NVIDIA RTX PRO 6000 Blackwell Max-Q, 96 GB each — `nvidia-smi` reports 97,887 MiB, i.e. **95.6 GiB usable per card**, 382.4 GiB combined |
| RAM | 512 GB (4 NUMA nodes) |
| vCPU | 80 (AMD EPYC, virtualised) |
| Storage | 800 GB scratch + 200 GB system (virtio, no NVMe passthrough) |
| OS | Ubuntu 26.04 |
| Driver | 595.71.05, compute capability 12.0 (sm120) |
| Interconnect | PCIe Gen 5 ×16, **no NVLink**, P2P working across all four cards |

## November 2026: the machine is back

Re-provisioned on 2026-11-06 with the same four cards and a fresh Ubuntu 26.04 image. What
changed against the August table above, and everything measured from here on, is on this
page and in the model directories below; the hardware findings further down still hold.

| | August 2026 | November 2026 |
|---|---|---|
| GPU | 4× RTX PRO 6000 Blackwell Max-Q, 97,887 MiB each | same — **95.6 GiB usable per card**, 382 GiB combined, 300 W per card (325 max) |
| RAM / vCPU | 512 GB, 80 | 503 GB, 64 (AMD EPYC, no AVX-512, 4 NUMA nodes) |
| Storage | 800 GB scratch + 200 GB system | 787 GB ephemeral disk at `/opt/llm` + 200 GB system; `/tmp` a 252 GB tmpfs |
| OS / kernel | Ubuntu 26.04 | Ubuntu 26.04, kernel 7.0.0-43 |
| Driver | 595.71.05 | **615.71.09**, open modules prebuilt by Ubuntu; CUDA 13.4, nvcc 13.4 |
| Interconnect | PCIe Gen 5 ×16, no NVLink, P2P | same, `nvidia-smi topo -p2p r` OK between all four |
| Engines | Docker + SGLang patchset, llama.cpp, vLLM | Docker 29 with nvidia-container-toolkit 1.20 (images on the ephemeral disk), `uv`, native llama.cpp b12167, Strata 0.2.11 |
| Network | Tailscale | public IPv4/IPv6, ufw with only 22/tcp open; model ports stay on `127.0.0.1` |

### Models measured, November 2026

| Model | Setup | Status |
|---|---|---|
| [DeepSeek-V4.1-Flash-1017](deepseek-v4-1-flash-1017/) · EXL3 3 bpw | [vLLM + EXL3, the pack's recipe, `PROFILE=8x REPLICA=0`](deepseek-v4-1-flash-1017/vllm-exl3/) | measured 2026-11-07 — **153 tok/s single stream, 1,510 tok/s at C=256**, prefill 13.3 k tok/s, 3/3 needles at 960k · 1.8–3.8× the two-card pack under load · NCCL all-reduce: this VM has no P2P atomics · [`q1`](deepseek-v4-1-flash-1017/vllm-exl3/scenarios/quality.md) on / off, measured 2026-11-08: MMLU-Pro 0.850 / 0.880, IFEval 0.955 / 0.860, HumanEval 0.994 / 0.945 |
| [DeepSeek-V4.1-Flash-1017](deepseek-v4-1-flash-1017/) · GSQ-RCO 2.25 bpw | [Strata 0.2.11, DeepSeek engine, `DS4_SPLIT=10,10,10,10`, 8 slots](deepseek-v4-1-flash-1017/strata/) | measured 2026-11-06 — **111.8 tok/s single stream**, decode 110 flat, prefill 4.1–4.3 k tok/s to 250k (3/3 needles); about 154 tok/s from C=4 on with one engine, **302 tok/s at C=8 with `--replicas 2`** · the DeepSeek engine does not batch · the automatic layer split leaves two cards empty, set `DS4_SPLIT` · [`q1`](deepseek-v4-1-flash-1017/strata/scenarios/quality.md) with thinking: **the best of the series** — IFEval 0.965, MMLU-Pro 0.890, HumanEval 0.994 |
| [DeepSeek-V4-Flash-0731](deepseek-v4-flash-0731/) · FP8 | [vLLM 0.33.0, unpatched, TP=4 + EP](deepseek-v4-flash-0731/vllm/) | measured 2026-11-07/08 — the August DeepGEMM blocker is gone in stock vLLM · 95 tok/s single stream, decode 92 flat, **170 with DSpark** · **3,869 tok/s at C=256, 5,956 at C=1024**, 34–40 % over the August SGLang patchset at the same levels · DSpark loses from 128 clients on · prefill 5.8–6.7 k tok/s, 3/3 at 250k · KV pool 1.56 M tokens · **four copies (DP=4 + EP) with one changed workspace constant: [11,535 tok/s at C=1024](deepseek-v4-flash-0731/vllm/scenarios/data-parallel.md)**, twice TP=4, the highest load figure on this machine · [`q1`](deepseek-v4-flash-0731/vllm/scenarios/quality.md) on / off: MMLU-Pro 0.870 / 0.790, IFEval 0.925 / 0.840, HumanEval 0.970 / 0.909 |
| [GLM-5.3-Flash](glm-5-3-flash/) · NVFP4 | [vLLM 0.33.0, TP=4 + EP, FP8 KV](glm-5-3-flash/vllm/) | measured 2026-11-06 — NVFP4 runs on sm120 with stock vLLM · **thinking cannot be switched off**, 376 tokens per answer at the default effort: 103.5 tok/s single stream, 1,088 tok/s and only **3.0 answers/s at C=256** (p50 86 s) · `reasoning_effort: low` cuts answers to 52 tokens, 2.8× the answer rate · decode 102 flat · prefill 6.4 k tok/s flat to 250k, 3/3 needles · [`q1`](glm-5-3-flash/vllm/scenarios/quality.md) low / max: MMLU-Pro 0.815 / 0.870, IFEval 0.810 / 0.880, HumanEval 0.939 / 0.970 |
| [Beam-1.0-501B-A23B](beam-1-0/) · NVFP4 | [vLLM 0.33.0, TP=4, FP8 KV](beam-1-0/vllm/) | measured 2026-11-07 — 98 tok/s single stream, decode 97–99 flat · **2,972 tok/s, 12.8 answers/s at C=256**, second only to MiMo · prefill 4.6–5.2 k tok/s, 3/3 needles at 250k · thinking always on, the effort budget barely moves it · [`q1`](beam-1-0/vllm/scenarios/quality.md) MMLU-Pro 0.890, IFEval 0.910, HumanEval 0.951; minimal effort within one standard error |
| [Hy3](hy3/) · FP8 | [vLLM 0.33.0, TP=4, FP8 KV](hy3/vllm/) | measured 2026-11-07 — 89.6 tok/s single stream, decode 85 flat · **2,254 tok/s, 4.4 answers/s at C=256**, every protocol answer at the 512-token cap at `reasoning_effort: high` · prefill 2.7 k falling to 1.8 k tok/s at 250k, 3/3 needles · KV pool 308 k tokens, 1.17 full-length requests · [`q1`](hy3/vllm/scenarios/quality.md) high / no_think: MMLU-Pro 0.880 / 0.795, IFEval 0.940 / 0.880, HumanEval 0.994 / 0.921 |
| [Nemotron-3-Super-120B-A12B](nemotron-3-super/) · NVFP4 | [vLLM 0.33.0, four copies (DP=4)](nemotron-3-super/vllm/) | measured 2026-11-07 — 83 tok/s single stream, decode 87 flat to 64k · **2,408 tok/s at C=256**, still rising · prefill 8.0 k tok/s on one card, 3/3 needles at 250k · 10.7 M tokens of cache per card · [`q1`](nemotron-3-super/vllm/scenarios/quality.md) IFEval 0.910, HumanEval 0.982, MMLU-Pro 0.830 |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) · FP8 | [vLLM 0.33.0, TP=4, stock image](mimo-v2-6-flash/vllm/) | measured 2026-11-06 — **3,650 output tok/s and 53.7 answers/s at C=256** with thinking on, 74.4 answers/s off, p50 under 5 s; still rising above it, [5,608 tok/s and 83 answers/s at C=1024](mimo-v2-6-flash/vllm/scenarios/concurrent-load.md#above-256-clients) (2026-11-08) · 140 tok/s single stream, decode 143 · prefill 6.1 k falling to 3.6 k tok/s at 250k, 3/3 needles · KV pool 4.3 M tokens · 1.20–1.23× the two-card machine · [`q1`](mimo-v2-6-flash/vllm/scenarios/quality.md): MMLU-Pro 0.775 / 0.850, IFEval 0.840 / 0.850, HumanEval 0.933 / 0.963 |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · IQ3_S GSQ-RCO and Q8_0 | [Strata 0.2.11, four-card layer split, 8 slots](qwen3-8-flash-next/strata/) | measured 2026-11-06 — **225 / 187 output tok/s single stream** (IQ3_S / Q8_0, the fastest in this repository), decode 222–254, **prefill 21,873 / 17,757 tok/s at 250k** (3/3 needles), 645 / 564 tok/s at C=8, queueing above 8 slots; cards at 20–34 % on the single stream · [`q1`](qwen3-8-flash-next/strata/scenarios/quality.md) both packs: the 3-bit pack trails the 8-bit ones by 5.5 points on MMLU-Pro without thinking (0.820 vs 0.875) and nowhere else; Q8_0 IFEval 0.945 on, HumanEval 0.982 on |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · FP8 | [vLLM 0.33.0, TP=4, Docker](qwen3-8-flash-next/vllm/) | measured 2026-11-06 — `v1`, both thinking arms, full ladder · **1,989 output tok/s at C=256**, [flat above it: 2,481 at C=1024](qwen3-8-flash-next/vllm/scenarios/concurrent-load.md#above-256-clients) with p50 86 s, 110 single stream (**175 with the MTP draft**), decode 115 (163–192 with draft) · prefill 7.6–7.8 k tok/s, 3/3 needles at 250k · KV pool 3.6 M tokens · [`q1`](qwen3-8-flash-next/vllm/scenarios/quality.md) both arms incl. **HumanEval 0.976** (Docker sandbox), IFEval 0.930, MMLU-Pro 0.885 / 0.860 — equal to the IQ3_S Strata run on Rocky 2× RTX PRO 4500 |

### November 2026, in one table

All on these four cards, thinking on, protocol `v1` for speed and `q1` for answers. Load
figures over the real run time ([why](../benchmark/README.md#the-window-overstates-slow-answers)).

| | Single stream | Best load figure | Prefill at 250k | MMLU-Pro | IFEval | HumanEval | Serve it for |
|---|---|---|---|---|---|---|---|
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/strata/) IQ3_S · Strata | **225 tok/s** | 722 tok/s at C=16 (8 slots) | **21,873 tok/s** | 0.860 | 0.910 | 0.988 | one to eight users, long documents |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/vllm/) FP8 · vLLM (+ MTP) | 110 (175) | 1,989 tok/s at C=256, 2,481 at 1,024 | 7,840 | 0.860 | 0.930 | 0.976 | a crowd that wants Qwen |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) FP8 · vLLM | 140 | 5,608 tok/s, **83 answers/s** at C=1024 | 3,561 | 0.850 | 0.850 | 0.963 | a crowd with short questions |
| [GLM-5.3-Flash](glm-5-3-flash/) NVFP4 · vLLM | 104 | 1,088 tok/s at 3.0 answers/s | 6,360 | 0.870 | 0.880 | 0.970 | only with `reasoning_effort: low` |
| [DeepSeek-V4.1-Flash](deepseek-v4-1-flash-1017/vllm-exl3/) EXL3 3 bpw · vLLM, pack recipe | 153 | 1,510 tok/s at C=256 | 13,264 | 0.850 | 0.955 | **0.994** | **top-group answers at three quarters of Qwen's throughput** |
| [DeepSeek-V4.1-Flash](deepseek-v4-1-flash-1017/strata/) 2.25 bpw · Strata | 112 | 302 tok/s at C=8 (2 replicas) | 4,159 | **0.890** | **0.965** | **0.994** | superseded by the EXL3 pack |
| [DeepSeek-V4-Flash-0731](deepseek-v4-flash-0731/vllm/) FP8 · vLLM | 95 (170 with DSpark) | **11,535 tok/s at C=1024** as four copies ¹; 5,956 at TP=4 | 5,844 | 0.870 | 0.925 | 0.970 | **the biggest crowd** |
| [Beam-1.0](beam-1-0/) NVFP4 · vLLM | 98 | 2,972 tok/s at C=256 | 4,616 | **0.890** | 0.910 | 0.951 | a crowd, with DeepSeek-level knowledge |
| [Hy3](hy3/) FP8 · vLLM | 90 | 2,254 tok/s at C=256 | 1,763 | 0.880 | 0.940 | **0.994** | hard questions, given time |
| [Nemotron-3-Super](nemotron-3-super/) NVFP4 · vLLM, 4 copies | 83 | 2,408 tok/s at C=256 | 6,597 (one card) | 0.830 | 0.910 | 0.982 | long contexts on one card per copy |
| [MiniMax-M3.1-Flash](minimax-m3-1-flash/) | — | — | — | — | — | — | does not run on sm120 |

¹ one constant changed in a mounted copy of vLLM's FlashInfer backend for DeepSeek-V4; see
[four copies](deepseek-v4-flash-0731/vllm/scenarios/data-parallel.md).

**No model wins every column, but one comes close.** DeepSeek's EXL3 pack on all four cards
answers in the top group — none of its `q1` values two standard errors below the best — at three
quarters of the throughput of Qwen under vLLM, and reads a million tokens of context. Strata with Qwen stays the fastest for a handful of users and
for long prompts up to 262k; MiMo under vLLM is the one to put in front of hundreds. GLM
matches Qwen on quality and loses to it on every speed column. DeepSeek-V4-Flash-0731 moves the
most tokens under load: 5,956 tok/s at 1,024 clients on stock vLLM, level with MiMo, and twice
that as four copies with one changed line — a step below V4.1 on answers. Hy3 answers at DeepSeek's level
and is the slowest to get there: ten times the tokens with thinking, and a cache for barely one
long document.

## Test list, November 2026

Requested 2026-11-06, each with throughput under protocol [`v1`](../benchmark/README.md) and
quality under `q1` (both thinking arms where the model has a switch; HumanEval runs in Inspect's
Docker sandbox). Sizes are the sum of the published files; with KV cache, activations and graphs
on top, **about 300 GB of weights is the practical ceiling at TP=4**: [Hy3](hy3/) at 301 GB still runs,
with cache for 1.17 requests of full length.

| Model | Variant measured | Engine | Status |
|---|---|---|---|
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) | FP8 (186 GB); GSQ-RCO IQ3_S and Q8_0 | vLLM 0.33 TP=4; Strata 0.2.11 | measured |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) | FP8 (178 GB) | vLLM 0.33 TP=4 | measured |
| [GLM-5.3-Flash](glm-5-3-flash/) | NVIDIA NVFP4 (204 GB); the FP8 original is 328 GB | vLLM 0.33 TP=4 + EP | measured |
| [MiniMax-M3.1-Flash](minimax-m3-1-flash/) | MXFP8 attention + NVFP4 experts (252 GB) | vLLM 0.33; SGLang 0.5.23; SGLang `dev-minimax-m31-flash` | **does not run on sm120**: MiniMax's sparse-attention kernels exist for SM100/SM103 only |
| [DeepSeek-V4.1-Flash-1017](deepseek-v4-1-flash-1017/) | the official FP8 is 510 GB and does not fit; [ISTA-DASLab GSQ-RCO 2.25 bpw](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF), 155 GB plus a 111 GB Engram table kept in host RAM | Strata 0.2.11, DeepSeek engine; and the [EXL3 3 bpw pack](https://huggingface.co/diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000) with its own vLLM recipe | measured |

## Models tested, August 2026

| Model | Cards | Setup | Output tok/s | Answers/s | At | Details |
|---|---|---|---|---|---|---|
| **DeepSeek-V4-Flash-0731** | 4 (TP/DP/EP) | SGLang + SM120 patchset · production | **4,438** | 14.25 req/s | C=1024 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |
| **Gemma-4-26B-A4B** | 1 | llama.cpp · SGLang · vLLM | 561.3 *(llama.cpp)* | **31.1** *(vLLM)* | C=32 | [`gemma-4-26b-a4b/`](gemma-4-26b-a4b/) |
| **Muse-Glimmer-30B** | 1 | llama.cpp | **312.2** | 0.76 | C=32 | [`muse-glimmer-30b/`](muse-glimmer-30b/) |
| **DeepSeek-V4-Flash-NVFP4** | 2 (TP) | vLLM B12X SM120 kit | **243.6** | 6.02 | C=256 | [`deepseek-v4-flash-nvfp4/`](deepseek-v4-flash-nvfp4/) |
| **Gemma-4-31B** | 1 | llama.cpp | **197.6** | 0.50 | C=8 | [`gemma-4-31b/`](gemma-4-31b/) |

Output tok/s and answers/s over the real run time, at the best level for each model
([why](../benchmark/README.md#the-window-overstates-slow-answers)).

**The Gemma-4-26B-A4B row is the one that cannot be read straight.** Its headline
31.1 answers/s is vLLM, which has no directory here — only the
[engine comparison](gemma-4-26b-a4b/engine-comparison.md), and that document recorded
answers per second under load but token throughput only at concurrency 1. The 561.3 tok/s
is the llama.cpp arm at the same level and a different engine. The two cells are not the
same measurement.

The three single-card models were measured on 2026-08-16, one per GPU; the NVFP4 row on
2026-08-17. Rows are ordered by output tokens per second, which is the metric the field
uses and the one that survives a difference in answer length — but the rows sit at
different concurrency levels, so even that column is not a ranking. It is not comparable
across rows without reading the scenario: the two DeepSeek rows and the two llama.cpp-only rows run with
thinking **on**, the Gemma-4-26B-A4B row with thinking **off** — a difference worth a factor
of 3.4 on its own — and the rows use one, two or four cards. The two DeepSeek rows are
additionally **different model releases**, not two setups of one model
([why that matters](deepseek-v4-flash-nvfp4/README.md#what-this-is-not-comparable-to)).
Within a row the comparison holds; across rows, follow the link.

---

## Machine findings

Everything here follows from this hardware and this host configuration. Check it
before planning a new evaluation on the machine — most of it will cost you a day
otherwise.

### SM120 is not a supported target for most inference stacks

Consumer and workstation Blackwell (RTX 50-series, RTX PRO 6000) uses compute
capability 12.0. Several kernel families that datacenter stacks rely on simply do not
exist for it. For DeepSeek-V4 the blocker was DeepGEMM's `tf32_hc_prenorm_gemm`,
which made vLLM and stock SGLang abort with `Assertion error: Unsupported
architecture`. Tracked in [DeepGEMM #317](https://github.com/deepseek-ai/DeepGEMM/issues/317)
and [vLLM #41063](https://github.com/vllm-project/vllm/issues/41063).

Expect to need a patched fork or a community image for any recent architecture — for a
while. By November stock vLLM 0.33 had closed this gap for DeepSeek-V4: it serves the 0731
checkpoint [unpatched](deepseek-v4-flash-0731/vllm/), faster than the August patchset, and
NVFP4 checkpoints run without help. The gaps that remain are narrower: MiniMax-M3.1's sparse
attention exists only for SM100/SM103, and FlashInfer's SM120 sparse-MLA decode does not fit
vLLM's fixed 128 MiB workspace when one card computes all 64 heads of DeepSeek-V4 — raising that
one constant gives [four copies at twice the throughput](deepseek-v4-flash-0731/vllm/scenarios/data-parallel.md).

### A model that fits one card changes which engine wins

The DeepSeek-V4 comparison was decided by tensor parallelism: llama.cpp could only
layer-split, so four cards worked one after another. That verdict does not transfer to
models small enough for a single card — there is nothing to split, and llama.cpp's
advantages (20 s start, plain upstream commit, no patched image) apply without the
penalty that decided the earlier comparison.

Four cards then serve four models rather than one, and the engine choice becomes a
question of measurement rather than of feasibility — and measured, it does **not** come
out in llama.cpp's favour once there is load. On Gemma-4-26B-A4B, one card, identical
workload, vLLM delivers 6.3× the answers per second at concurrency 32 *and* better
latency, holding the card at 100 % where llama.cpp falls to 32 %
([engine comparison](gemma-4-26b-a4b/engine-comparison.md)). For a single user the three
engines are within 14 % of each other; the gap is entirely in batching.

A single-architecture build from current master takes about two minutes here, so
checking a same-day commit is cheaper than reasoning about which release added support:

```bash
docker build --build-arg LLAMA_COMMIT=$(git ls-remote \
    https://github.com/ggml-org/llama.cpp.git HEAD | cut -f1) \
    -t llamacpp-sm120:$(date +%Y%m%d) .
```

### KV cache is what runs out, not weights

On a 97 GB card a 31 B model in BF16 leaves room that looks generous until the context
is sized. Measured on Gemma-4-31B with flash attention on:

| `-c` | KV cache | total | result |
|---|---|---|---|
| 32,768 | ~19 GB | 82.1 GB | runs, 15 GB spare |
| 65,536 | **38.4 GB** | > 97 GB | `cudaMalloc failed: out of memory` at load |

Doubling the context doubles the KV allocation, and the failure lands at model-load
time with a clear message — but only if you read the container log, since the process
exits rather than degrading. Size `-c` against the slot count you need
(`-c` ÷ `-np` is the per-slot budget) rather than against what the card looks like it
can hold.

**And the context length is not the only thing that sizes it.** On the NVFP4 DeepSeek
checkpoint, changing a *scheduling* flag — `--max-num-batched-tokens` — moved the KV pool
by 56 % at unchanged VRAM, because that flag also sizes a per-token fp32 state cache. Same
cards, same weights, same `--gpu-memory-utilization`, 1.07 M tokens against 1.66 M. So a
pool that looks too small is not automatically evidence that the weights are too big —
check what else the batch budget pays for
([measurement](deepseek-v4-flash-nvfp4/vllm-b12x/README.md#the-kv-pool-is-set-by-the-batch-budget-not-by-vram)).

### Single-stream speed does not scale with GPU count

Decode is interconnect-latency bound and this machine has no NVLink. More cards buy
concurrency and KV capacity, not faster individual answers. In practice TP=4 wins
aggregate throughput while TP=2 wins single-request latency, because fewer PCIe hops
are involved.

### The machine is a VM

CPU topology is synthetic (80 "sockets" × 1 core, generic model string), disks are
virtio, GPUs report no NUMA node (`numa_node = -1`), and all NUMA distances are
uniform. NUMA pinning, CPU affinity and PCIe-root placement advice from bare-metal
guides has no effect here.

### Host firewall blocks container-to-host traffic

With `ufw` active and `deny (incoming)`, containers cannot reach host ports — not
even via `host.docker.internal`. A rule limited to Docker's private ranges is needed:

```bash
sudo ufw allow from 172.16.0.0/12 to any port 8000 proto tcp
```

### Single-architecture builds are cheap here

Building for `-DCMAKE_CUDA_ARCHITECTURES=120` alone takes under two minutes on the 80
vCPUs, so there is little reason to carry a generic multi-arch binary.

---

*Hardware as of August 2026 · driver 595.71.05 · Ubuntu 26.04 — back in service November 2026, driver 615.71.09, see the top of this page*
