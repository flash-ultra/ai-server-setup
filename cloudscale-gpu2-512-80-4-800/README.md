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
| [GLM-5.3-Flash](glm-5-3-flash/) · NVFP4 | [vLLM 0.33.0, TP=4 + EP, FP8 KV](glm-5-3-flash/vllm/) | measured 2026-11-06 — NVFP4 runs on sm120 with stock vLLM · **thinking cannot be switched off**, 376 tokens per answer at the default effort: 103.5 tok/s single stream, 2,347 tok/s but only **6.4 answers/s at C=256** (p50 86 s) · `reasoning_effort: low` cuts answers to 52 tokens, 2.8× the answer rate · decode 102 flat · prefill 6.4 k tok/s flat to 250k, 3/3 needles |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) · FP8 | [vLLM 0.33.0, TP=4, stock image](mimo-v2-6-flash/vllm/) | measured 2026-11-06 — **3,740 output tok/s and 55 answers/s at C=256** with thinking on, 75.6 answers/s off, p50 under 5 s · 140 tok/s single stream, decode 143 · prefill 6.1 k falling to 3.6 k tok/s at 250k, 3/3 needles · KV pool 4.3 M tokens · 1.19–1.23× the two-card machine · [`q1`](mimo-v2-6-flash/vllm/scenarios/quality.md): MMLU-Pro 0.775 / 0.850, IFEval 0.840 / 0.850, HumanEval 0.933 / 0.963 |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · IQ3_S GSQ-RCO and Q8_0 | [Strata 0.2.11, four-card layer split, 8 slots](qwen3-8-flash-next/strata/) | measured 2026-11-06 — **225 / 187 output tok/s single stream** (IQ3_S / Q8_0, the fastest in this repository), decode 222–254, **prefill 21,873 / 17,757 tok/s at 250k** (3/3 needles), 645 / 564 tok/s at C=8, queueing above 8 slots; cards at 20–34 % on the single stream · [`q1`](qwen3-8-flash-next/strata/scenarios/quality.md) both packs: the 3-bit pack trails the 8-bit ones by 5.5 points on MMLU-Pro without thinking (0.820 vs 0.875) and nowhere else; Q8_0 IFEval 0.945 on, HumanEval 0.982 on |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · FP8 | [vLLM 0.33.0, TP=4, Docker](qwen3-8-flash-next/vllm/) | measured 2026-11-06 — `v1`, both thinking arms, full ladder · **2,275 output tok/s at C=256**, 110 single stream (**175 with the MTP draft**), decode 115 (163–192 with draft) · prefill 7.6–7.8 k tok/s, 3/3 needles at 250k · KV pool 3.6 M tokens · [`q1`](qwen3-8-flash-next/vllm/scenarios/quality.md) both arms incl. **HumanEval 0.976** (Docker sandbox), IFEval 0.930, MMLU-Pro 0.885 / 0.860 — equal to the IQ3_S Strata run on Rocky 2× RTX PRO 4500 |

## Test list, November 2026

The two-card cloudscale machine ([`GPU2-256-40-2-1600`](../../dist/cloudscale-gpu2-256-40-2-1600/README.md), the same RTX PRO 6000 twice instead of four times) has already measured MiMo-V2.6-Flash-RL, DeepSeek-V4.1-Flash-1017 as EXL3 and Qwen3.8-Flash-Next as UD-Q6_K_XL under the same protocols; those are the reference columns for the rows below.

Requested 2026-11-06, each with throughput under protocol
[`v1`](../../dist/benchmark/README.md) and quality under `q1`
(GSM8K, MMLU-Pro, IFEval, both thinking arms where the model has a switch; HumanEval
becomes possible here because Docker gives Inspect a sandbox). Sizes are the sum of the
published `.safetensors`; the budget is 382 GiB minus KV cache, activations and graphs,
so **roughly 280 GB of weights is the practical ceiling at TP=4.**

| # | Model | Published weights | Fits? | Engine to try first | Notes |
|---|---|---|---|---|---|
| 1 | [Qwen3.8-Flash-Next-FP8](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8) · 125B-A6B + 51B n-gram + 4B MTP | 186 GB FP8 | **yes**, 47 GB/card | vLLM ≥ 0.32 (`Qwen4Exp`), SGLang ≥ 0.5.22 | the model that runs as IQ3_S under Strata on Rocky 2× RTX PRO 4500 (141 tok/s single stream, MMLU-Pro 0.895): first FP8 numbers and a `q1` on the 3-bit question. BF16 (360 GB) does not fit. The requested `Qwen3.8-Flash-Nextest` does not exist on the Hub (404 with the token) — read as Flash-Next |
| 2 | [MiMo-V2.6-Flash-RL](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) · 309B-A15B, 1M context, text + image + video + audio, MTP drafter | 178 GB FP8 | **yes**, 45 GB/card | vLLM ≥ 0.32 (MiMo-V2.6 FP8 KV fix), SGLang ≥ 0.5.21; the card's own image is `vllm/vllm-openai:mimov25-cu129` | from the [mimo-v26 collection](https://huggingface.co/collections/XiaomiMiMo/mimo-v26): `-MOPD` is the same size (distilled variant), `-Pro-RL` is 573 GB and out, `-Distill-Qwen-9B` (19 GB, dense) fits one card and is a cheap extra |
| 3 | [GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) · 320B-A18B, hybrid sparse + linear attention, mHC | 328 GB FP8 | **borderline**: 82 GB/card, ~13 GB left for KV | [`nvidia/GLM-5.3-Flash-NVFP4`](https://huggingface.co/nvidia/GLM-5.3-Flash-NVFP4) (official ModelOpt, "NVIDIA Blackwell", **204 GB**, 51 GB/card) under vLLM `--tensor-parallel-size 4 --enable-expert-parallel --kv-cache-dtype fp8` or SGLang `--quantization modelopt_fp4 --tp-size 4` | the FP8 original only as a fit probe with FP8 KV (vLLM 0.33 default for this model) and a short context; NVFP4 is the serving candidate. MIT licence |
| 4 | [MiniMax-M3.1-Flash](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) · 428B-A23B per card, MiniMax Sparse Attention, 1M context, text + image + video, DSpark draft head | 252 GB MXFP8 | **yes**, 63 GB/card | SGLang 0.5.23 (lists M3.1-Flash explicitly), then vLLM (`MiniMaxM3Sparse…` rows exist for M3 / M3-MXFP8, M3.1 not named) | the risk is MXFP8 and the MSA kernels on sm_120; vLLM 0.33 mentions a CUTLASS MSA decode kernel. Released 2026-11-05, so the engines are fresh |
| 5 | [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) (the latest V4) | 510 GB FP8 | **no** | GGUF only: [`ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF`](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF) (the quant family Strata serves) or `unsloth/…-GGUF` under llama.cpp built with nvcc 13.4 | the FP8 path exists on sm_120 (SGLang 0.5.20: "DeepSeek-V4 on RTX PRO 6000"), but the weights are 130 GB over the budget. Optional regression: [DeepSeek-V4-Flash-0731](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) (167 GB FP8), measured on the predecessor at 6,454 tok/s C=768 with a patched SGLang — stock SGLang now |
| 5c | DeepSeek-V4.1-Flash-1017 · **EXL3 3 bpw** | [`diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000`](https://huggingface.co/diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000), 315 GiB incl. DSpark drafter | yes | the pack's own vLLM + `vllm_exl3` recipe (sm120 kernels built in the image, no GPU needed for the build) | measured on the two-card cloudscale machine at 136.5 tok/s single stream and 11,386 tok/s prefill ([page](../../dist/cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/README.md)); here first at TP=2 on two cards (same cards, direct replication), then TP=4 if the plugin takes it |
| 6 | [Ling-3.1-flash-1019](https://huggingface.co/inclusionAI/Ling-3.1-flash-1019) · `BailingMoeV3` hybrid MoE, 572 B | 574 GB FP8 | **no** as published | GGUF by [bartowski](https://huggingface.co/bartowski/Ling-3.1-flash-1019-GGUF) under llama.cpp: **IQ4_XS 317 GB** (4.25 bpw, imatrix) leaves ~22 GB per card for KV; Q3_K_M 275 GB as the roomier fallback | added 2026-11-06 at the user's request; same engine build as DeepSeek, so it queues behind it |
| 1b | Qwen3.8-Flash-Next · **Strata** | IQ3_S GSQ-RCO (54.8 + 28.8 GB), the Rocky 2× RTX PRO 4500 setup | yes | Strata v0.2.x, four-card layer split, up to 8 slots | engine comparison on the same machine: Strata with its MTP draft against vLLM FP8 |
| 5b | DeepSeek-V4.1-Flash-1017 · **Strata** | [GSQ-RCO 2.25 bpw](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF): 155 GB backbone + 111 GB Engram | yes: experts all resident, Engram in RAM | Strata `--family deepseek41`, DSpark drafter `--dspark auto`, `--parallel` up to 8 | the second DeepSeek path next to llama.cpp; `q1` on both to price the 2.25 bits |

Order: 1 → 2 → 3 → 4 → 5 → 6, then the two Strata runs (1b, 5b), which need their own build and the cards to themselves. The first two are plain FP8 under engines that name them;
the third and fourth depend on Blackwell kernels for NVFP4 and MXFP8; the fifth and sixth need a
GGUF engine built on the machine. Engines go on as Docker images (`vllm/vllm-openai:v0.33.0`,
CUDA 13.0 only; `lmsysorg/sglang:v0.5.23`) with `/opt/llm/hf` mounted, llama.cpp native.

## Models tested, August 2026

| Model | Cards | Setup | Output tok/s | Answers/s | At | Details |
|---|---|---|---|---|---|---|
| **DeepSeek-V4-Flash-0731** | 4 (TP/DP/EP) | SGLang + SM120 patchset · production | **6,453.6** | 19.65 req/s | C=768 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |
| **Gemma-4-26B-A4B** | 1 | llama.cpp · SGLang · vLLM | 816.9 *(llama.cpp)* | **31.88** *(vLLM)* | C=32 | [`gemma-4-26b-a4b/`](gemma-4-26b-a4b/) |
| **Muse-Glimmer-30B** | 1 | llama.cpp | **520.5** | 1.27 | C=32 | [`muse-glimmer-30b/`](muse-glimmer-30b/) |
| **DeepSeek-V4-Flash-NVFP4** | 2 (TP) | vLLM B12X SM120 kit | **403.6** | 9.97 | C=256 | [`deepseek-v4-flash-nvfp4/`](deepseek-v4-flash-nvfp4/) |
| **Gemma-4-31B** | 1 | llama.cpp | **310.2** | 0.80 | C=32 | [`gemma-4-31b/`](gemma-4-31b/) |

**The Gemma-4-26B-A4B row is the one that cannot be read straight.** Its headline
31.88 answers/s is vLLM, which has no directory here — only the
[engine comparison](gemma-4-26b-a4b/engine-comparison.md), and that document recorded
answers per second under load but token throughput only at concurrency 1. The 816.9 tok/s
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

Expect to need a patched fork or a community image for any recent architecture.

### A model that fits one card changes which engine wins

The DeepSeek-V4 comparison was decided by tensor parallelism: llama.cpp could only
layer-split, so four cards worked one after another. That verdict does not transfer to
models small enough for a single card — there is nothing to split, and llama.cpp's
advantages (20 s start, plain upstream commit, no patched image) apply without the
penalty that decided the earlier comparison.

Four cards then serve four models rather than one, and the engine choice becomes a
question of measurement rather than of feasibility — and measured, it does **not** come
out in llama.cpp's favour once there is load. On Gemma-4-26B-A4B, one card, identical
workload, vLLM delivers 5.9× the answers per second at concurrency 32 *and* better
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
