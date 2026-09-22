# cloudscale.ch `GPU2-256-40-2-1600`

2× RTX PRO 6000 Blackwell Max-Q in a fully virtualised KVM guest. The successor to
[`GPU2-512-80-4-800`](../cloudscale-gpu2-512-80-4-800/README.md), with half the cards.
Everything below was measured on this machine.

| | |
|---|---|
| Provider | cloudscale.ch, flavour `GPU2-256-40-2-1600` |
| GPU | 2× NVIDIA RTX PRO 6000 Blackwell Max-Q, 96 GB each — `nvidia-smi` reports 97,887 MiB, i.e. **95.6 GiB usable per card**, 191.2 GiB combined |
| RAM | 251 GB |
| vCPU | 40 (virtualised) |
| Storage | 1.6 TB scratch (`/dev/sdb`) + 193 GB system |
| OS | Ubuntu 26.04 |
| Driver | 595.84, **open kernel modules**, compute capability 12.0 (sm120) |
| Interconnect | PCIe PHB, **no NVLink** |

## Models tested

All figures at concurrency 256, the top of the ladder.

| Model | Cards | Setup | Output tok/s | Answers/s | Tok/answer | Details |
|---|---|---|---|---|---|---|
| **MiniMax-M2.5-NVFP4** | 2 (TP) | vLLM 0.28.0 | **2,947–3,126** | 9.65–9.75 | 258 | [`minimax-m2-5/`](minimax-m2-5/) |
| **Qwen3.8-Flash-Next** Q6_K_XL | 2 (layer split) | llama.cpp master, 6 slots | **1,390** | 7.47 | 186 | [`qwen3-8-flash-next/`](qwen3-8-flash-next/) · **images** |
| **DeepSeek-V4-Flash-0731** | 2 (TP) | SGLang + SM120 patchset | **1,173–1,183** | 32.58–32.65 | 35 | [`deepseek-v4-flash-0731/`](deepseek-v4-flash-0731/) |

**Output tokens per second leads because it is the metric the rest of the field uses**,
and because answers per second is not comparable across these rows: the tokens-per-answer
column spans a factor of seven. The 0731 setup runs with thinking **off** by default and
replies in 35 tokens, MiniMax cannot switch thinking off and writes 258, Qwen writes 186.
Ranked by answers per second 0731 leads by 4×; ranked by tokens per second it comes last.
Both are correct measurements of different things.

**Neither column is a verdict.** The rows do not share a thinking state, and at equal
thinking state 0731 and MiniMax change places at concurrency 32. Latency is missing from
this table entirely and is where the setups differ most — 7.96 s for 0731 against 133.9 s
for Qwen at this concurrency. Follow the link before comparing any two rows.

## Trials

Engines evaluated and not adopted live in [`trials/`](trials/). Nothing there is protocol
`v1`, and its numbers never enter the table above.

| Trial | Verdict |
|---|---|
| [FreeToken](trials/freetoken.md) | Not for production serving; viable as a second model on the otherwise idle card |

## Machine findings

### Two cards set a hard ceiling on model size

The binding constraint is weights, not KV cache. Measured per card against the
95.6 GiB the driver actually offers:

| Checkpoint | Weights per card | Fits |
|---|---|---|
| Qwen3.6-35B-A3B FP8 | 17.5 GiB | yes |
| MiniMax-M2.5 NVFP4 | 65.2 GiB | yes |
| DeepSeek-V4-Flash NVFP4 | 73.1 GiB | yes, at `--gpu-memory-utilization 0.93` |
| GLM-5.3-Flash GGUF IQ4_XS | 73.0 GiB | yes, llama.cpp only |
| Qwen3.5-122B-A10B FP8 | 59.3 GiB | yes |
| Qwen3.8-Flash-Next GGUF UD-Q5_K_XL | 73.7 GiB | yes, llama.cpp only |
| Qwen3.8-Flash-Next GGUF UD-Q6_K_XL | 78.8 GiB | yes, llama.cpp only |
| GLM-5.3-Flash NVFP4 | 90.7 GiB | **no** — nothing left for KV |
| Qwen3.5-397B-A17B NVFP4 | 117.0 GiB | **no** — exceeds both cards combined |

The two GGUF rows are the checkpoint size divided by two cards, like every other row.
What llama.cpp actually places on the cards is
[34.6 GiB less](qwen3-8-flash-next/llama-cpp/README.md#weights-on-disk-are-346-gib-larger-than-weights-in-vram)
in both cases — so these rows are conservative, and the real headroom is larger.

**Nothing fits beside DeepSeek-V4-Flash.** It needs `--mem-fraction-static 0.93`; at
`0.85` it aborts with `ValueError: No available memory for the cache blocks` after
loading the weights, and `restart: unless-stopped` then puts the container into a restart
loop. That leaves about 7 GiB per card, and the smallest useful vision model needs 11.

**That is a property of this checkpoint, not of the machine.** Qwen3.8-Flash-Next at
UD-Q6_K_XL with six full-length slots leaves 10.6 and 15.7 GiB free, and at Q5 with one
slot it left roughly 31 and 36 GiB. Whether a second model fits depends entirely on which
first model is chosen — an earlier version of this page stated the DeepSeek case as a
general rule, which it is not.

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

**Two unrelated models now measure the same ceiling.** GLM-5.3-Flash (45 layers, denser
activation) and Qwen3.8-Flash-Next (10 of 512 experts, micro-block sparse attention) both
pin in the **forties** under llama.cpp at every concurrency level from 1 to 256 —
39–47 % across everything measured here, and 55–61 % during prefill, which is the only
phase that escapes it. It is the engine, not the architecture, and not the configuration
either: the range holds across two quantisations and slot counts of 1, 4 and 6.

Consequence for planning: any model that only runs under llama.cpp on this machine pays
**in latency, not in token throughput**. Measured at concurrency 256 against
DeepSeek-V4-Flash-0731 under SGLang on the same cards:

| | llama.cpp · Qwen3.8-Flash-Next | SGLang · DSv4-0731 |
|---|---|---|
| Output tok/s | **1,390.3** | 1,173.2 |
| Answers/s | 7.47 | **32.58** |
| Tokens per answer | 186 | 35 |
| Latency p50 | 133.9 s | **7.96 s** |

The factor of 17 in latency is the cost. The factor of 4.4 in answers per second is
mostly answer length — the two setups do not produce comparable replies — and in tokens
per second llama.cpp is ahead here. An earlier version of this page reported a
"factor of 5 in throughput" from the answers-per-second column alone; that reading was
wrong, and the single-slot configuration it was measured on made it worse.

**Every multimodal model that fits on these two cards runs only under llama.cpp.** That is
what images cost here.

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
