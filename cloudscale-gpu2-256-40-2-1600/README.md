# cloudscale.ch `GPU2-256-40-2-1600`

2× RTX PRO 6000 Blackwell Max-Q in a fully virtualised KVM guest. The successor to
[`GPU2-512-80-4-800`](../cloudscale-gpu2-512-80-4-800/README.md), with half the cards.
Everything below was measured on this machine.

| | |
|---|---|
| Provider | cloudscale.ch, flavour `GPU2-256-40-2-1600` |
| GPU | 2× NVIDIA RTX PRO 6000 Blackwell Max-Q, 97,887 MiB each (195,774 MiB total) |
| RAM | 251 GB |
| vCPU | 40 (virtualised) |
| Storage | 1.6 TB scratch (`/dev/sdb`) + 193 GB system |
| OS | Ubuntu 26.04 |
| Driver | 595.84, **open kernel modules**, compute capability 12.0 (sm120) |
| Interconnect | PCIe PHB, **no NVLink** |

## Models tested

| Model | Cards | Setup | Peak measured | Details |
|---|---|---|---|---|
| **DeepSeek-V4-Flash-0731** | 2 (TP) | SGLang + SM120 patchset | 32.58–32.65 answers/s @ C=256 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |
| **MiniMax-M2.5-NVFP4** | 2 (TP) | vLLM 0.28.0 | 9.65–9.75 answers/s @ C=256 | [`minimax-m2-5/`](minimax-m2-5/) |

**The peak column is not a ranking.** The 0731 row was measured with thinking **off** — the
default of that setup — and answers at 35 tokens; the MiniMax row cannot switch thinking off
and answers at 258. At equal thinking state the order reverses at concurrency 32. Follow the
link before comparing the two.

## Machine findings

### Two cards set a hard ceiling on model size

The binding constraint is weights, not KV cache. Measured per card (102.6 GB usable):

| Checkpoint | Weights per card | Fits |
|---|---|---|
| Qwen3.6-35B-A3B FP8 | 17.5 GiB | yes |
| MiniMax-M2.5 NVFP4 | 65.2 GiB | yes |
| DeepSeek-V4-Flash NVFP4 | 73.1 GiB | yes, at `--gpu-memory-utilization 0.93` |
| GLM-5.3-Flash GGUF IQ4_XS | 73.0 GiB | yes, llama.cpp only |
| Qwen3.5-122B-A10B FP8 | 59.3 GiB | yes |
| GLM-5.3-Flash NVFP4 | 90.7 GiB | **no** — nothing left for KV |
| Qwen3.5-397B-A17B NVFP4 | 117.0 GiB | **no** — exceeds both cards combined |

**Two models never fit together.** DeepSeek-V4-Flash needs `0.93`; at `0.85` it aborts
with `ValueError: No available memory for the cache blocks` after loading the weights,
and `restart: unless-stopped` then puts the container into a restart loop. That leaves
about 7 GB per card, and the smallest useful vision model needs 11.

### llama.cpp cannot split across these cards

`-sm row` fails at load:

```
llama_model_load: error loading model: device CUDA0 does not support split buffers
```

The obvious suspicion — that IQ-type quantisations lack split-buffer support while
K-quants have it — is **wrong**: `UD-Q3_K_XL` produces the identical message. It is the
CUDA backend on this card, not the file format. Only `-sm layer` loads, so the cards
work in turn rather than together, and GPU utilisation sits near half of what vLLM
reaches on the same hardware.

Consequence for planning: any model that only runs under llama.cpp on this machine pays
roughly a factor of 3 on generation and 20 on prompt processing against a vLLM path.

```
prefill, tokens per second        0                              10500

llama.cpp  GLM-5.3-Flash    530   █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
vLLM       MiniMax-M2.5  10 516   ██████████████████████████████████████


generation at long context        0                                 75

llama.cpp  GLM-5.3-Flash     22   ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░
vLLM       MiniMax-M2.5   63–74   ████████████████████████████████████░░
```

Two different models, so this is not a model comparison — it is what the engine costs on
this hardware. Both ran on the same two cards with the same driver. The GPU utilisation
tells the same story from the other side: llama.cpp with `-sm layer` leaves one card idle
much of the time, vLLM holds both at 100 % even on a single request.

### Standard vLLM works here — the sm120 failure was model-specific

`vllm/vllm-openai:v0.28.0` runs unpatched on these cards. The
[DeepSeek-V4 sm120 blocker](../cloudscale-gpu2-512-80-4-800/README.md) came from that
model's hardwired MHC kernels reaching DeepGEMM, not from vLLM or the GPU. Checked
against the registry before committing to a build:

```
Qwen3_5MoeForConditionalGeneration -> True
MiniMaxM2ForCausalLM              -> True
Qwen4ExpForConditionalGeneration  -> False   (Qwen3.8-Flash-Next, released 2026-08-27)
Glm5NextForConditionalGeneration  -> False   (GLM-5.3-Flash, released 2026-08-27)
```

A registry check costs 30 seconds and no GPU. Do it before downloading 150 GB.
