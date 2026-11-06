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
| [GLM-5.3-Flash](glm-5-3-flash/) · NVFP4 | [vLLM 0.33.0, TP=4 + EP, FP8 KV](glm-5-3-flash/vllm/) | measured 2026-11-06 — NVFP4 runs on sm120 with stock vLLM · **thinking cannot be switched off**, 376 tokens per answer at the default effort: 103.5 tok/s single stream, 2,347 tok/s but only **6.4 answers/s at C=256** (p50 86 s) · `reasoning_effort: low` cuts answers to 52 tokens, 2.8× the answer rate · decode 102 flat · prefill 6.4 k tok/s flat to 250k, 3/3 needles · [`q1`](glm-5-3-flash/vllm/scenarios/quality.md) low / max: MMLU-Pro 0.815 / 0.870, IFEval 0.810 / 0.880, HumanEval 0.939 / 0.970 |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) · FP8 | [vLLM 0.33.0, TP=4, stock image](mimo-v2-6-flash/vllm/) | measured 2026-11-06 — **3,740 output tok/s and 55 answers/s at C=256** with thinking on, 75.6 answers/s off, p50 under 5 s · 140 tok/s single stream, decode 143 · prefill 6.1 k falling to 3.6 k tok/s at 250k, 3/3 needles · KV pool 4.3 M tokens · 1.19–1.23× the two-card machine · [`q1`](mimo-v2-6-flash/vllm/scenarios/quality.md): MMLU-Pro 0.775 / 0.850, IFEval 0.840 / 0.850, HumanEval 0.933 / 0.963 |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · IQ3_S GSQ-RCO and Q8_0 | [Strata 0.2.11, four-card layer split, 8 slots](qwen3-8-flash-next/strata/) | measured 2026-11-06 — **225 / 187 output tok/s single stream** (IQ3_S / Q8_0, the fastest in this repository), decode 222–254, **prefill 21,873 / 17,757 tok/s at 250k** (3/3 needles), 645 / 564 tok/s at C=8, queueing above 8 slots; cards at 20–34 % on the single stream · [`q1`](qwen3-8-flash-next/strata/scenarios/quality.md) both packs: the 3-bit pack trails the 8-bit ones by 5.5 points on MMLU-Pro without thinking (0.820 vs 0.875) and nowhere else; Q8_0 IFEval 0.945 on, HumanEval 0.982 on |
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) · FP8 | [vLLM 0.33.0, TP=4, Docker](qwen3-8-flash-next/vllm/) | measured 2026-11-06 — `v1`, both thinking arms, full ladder · **2,275 output tok/s at C=256**, 110 single stream (**175 with the MTP draft**), decode 115 (163–192 with draft) · prefill 7.6–7.8 k tok/s, 3/3 needles at 250k · KV pool 3.6 M tokens · [`q1`](qwen3-8-flash-next/vllm/scenarios/quality.md) both arms incl. **HumanEval 0.976** (Docker sandbox), IFEval 0.930, MMLU-Pro 0.885 / 0.860 — equal to the IQ3_S Strata run on Rocky 2× RTX PRO 4500 |

## Test list, November 2026

Requested 2026-11-06, each with throughput under protocol [`v1`](../benchmark/README.md) and
quality under `q1` (both thinking arms where the model has a switch; HumanEval runs in Inspect's
Docker sandbox). Sizes are the sum of the published files; with KV cache, activations and graphs
on top, **about 280 GB of weights is the practical ceiling at TP=4**.

| Model | Variant measured | Engine | Status |
|---|---|---|---|
| [Qwen3.8-Flash-Next](qwen3-8-flash-next/) | FP8 (186 GB); GSQ-RCO IQ3_S and Q8_0 | vLLM 0.33 TP=4; Strata 0.2.11 | measured |
| [MiMo-V2.6-Flash-RL](mimo-v2-6-flash/) | FP8 (178 GB) | vLLM 0.33 TP=4 | measured |
| [GLM-5.3-Flash](glm-5-3-flash/) | NVIDIA NVFP4 (204 GB); the FP8 original is 328 GB | vLLM 0.33 TP=4 + EP | measured |
| [MiniMax-M3.1-Flash](minimax-m3-1-flash/) | MXFP8 attention + NVFP4 experts (252 GB) | vLLM 0.33; SGLang 0.5.23; SGLang `dev-minimax-m31-flash` | **does not run on sm120**: MiniMax's sparse-attention kernels exist for SM100/SM103 only |
| DeepSeek-V4.1-Flash-1017 | the official FP8 is 510 GB and does not fit; [ISTA-DASLab GSQ-RCO 2.25 bpw](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF), 155 GB plus a 111 GB Engram table kept in host RAM | the same files under Strata and under llama.cpp b12167 (`deepseek41`) | planned. The [EXL3 pack](../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/) is built for two cards and measured there |
| Ling-3.1-flash-1019 | 572 B, FP8 574 GB does not fit; [bartowski](https://huggingface.co/bartowski/Ling-3.1-flash-1019-GGUF) IQ4_XS, 317 GB | llama.cpp b12167 (`bailingmoe3`) | planned |

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
