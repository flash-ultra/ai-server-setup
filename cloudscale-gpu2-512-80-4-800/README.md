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

| Model | Production setup | Peak throughput | Details |
|---|---|---|---|
| **DeepSeek-V4-Flash-0731** | SGLang + SM120 patchset | 27,026 total tok/s @ C=256 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |

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
