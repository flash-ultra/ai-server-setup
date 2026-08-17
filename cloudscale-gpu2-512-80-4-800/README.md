# cloudscale.ch `GPU2-512-80-4-800`

4× RTX PRO 6000 Blackwell Max-Q in a fully virtualised KVM guest. Everything below
was measured on this machine.

| | |
|---|---|
| Provider | cloudscale.ch, flavour `GPU2-512-80-4-800` |
| GPU | 4× NVIDIA RTX PRO 6000 Blackwell Max-Q, 97,887 MiB each (389,007 MiB total) |
| RAM | 512 GB (4 NUMA nodes) |
| vCPU | 80 (AMD EPYC, virtualised) |
| Storage | 800 GB scratch + 200 GB system (virtio, no NVMe passthrough) |
| OS | Ubuntu 26.04 |
| Driver | 595.71.05, compute capability 12.0 (sm120) |
| Interconnect | PCIe Gen 5 ×16, **no NVLink**, P2P working across all four cards |

## Models tested

| Model | Cards | Setup | Peak measured | Details |
|---|---|---|---|---|
| **DeepSeek-V4-Flash-0731** | 4 (TP/DP/EP) | SGLang + SM120 patchset · production | 19.65 req/s @ C=768 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |
| **DeepSeek-V4-Flash-NVFP4** | 2 (TP) | vLLM B12X SM120 kit | 9.97 answers/s @ C=256 | [`deepseek-v4-flash-nvfp4/`](deepseek-v4-flash-nvfp4/) |
| **Gemma-4-26B-A4B** | 1 | llama.cpp · SGLang · vLLM | **31.88 answers/s @ C=32** (vLLM) | [`gemma-4-26b-a4b/`](gemma-4-26b-a4b/) |
| **Gemma-4-31B** | 1 | llama.cpp | 0.80 answers/s @ C=32 | [`gemma-4-31b/`](gemma-4-31b/) |
| **Muse-Glimmer-30B** | 1 | llama.cpp | 1.27 answers/s @ C=32 | [`muse-glimmer-30b/`](muse-glimmer-30b/) |

The three single-card models were measured on 2026-08-16, one per GPU; the NVFP4 row on
2026-08-17. **The peak column is not a ranking.** It is not comparable across rows without
reading the scenario: the two DeepSeek rows and the two llama.cpp-only rows run with
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

*Hardware as of August 2026 · driver 595.71.05 · Ubuntu 26.04*
