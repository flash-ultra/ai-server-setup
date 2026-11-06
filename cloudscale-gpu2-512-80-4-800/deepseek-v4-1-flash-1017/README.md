# DeepSeek-V4.1-Flash-1017 · GSQ-RCO 2.25 bpw

DeepSeek's 763 B mixture-of-experts on all four cards of [this machine](../README.md),
measured 2026-11-06. The official FP8 checkpoint is 510 GB and does not fit 382 GiB, so
this is ISTA-DASLab's 2.25-bit GSQ-RCO set under Strata's DeepSeek engine. The
[EXL3 3-bit pack on the two-card machine](../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/README.md)
is the reference.

| | |
|---|---|
| Checkpoint | [`ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF`](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF) IQ2_XS, **2.25 bpw** — 155 GB of model, a 111 GB Engram n-gram table (IQ4_NL) and the 8 GB DSpark drafter |
| Base | [`deepseek-ai/DeepSeek-V4.1-Flash-1017`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), 763 B total, 384 routed experts, 6 active, 40 layers |
| Setup | [Strata 0.2.11 with its DeepSeek engine `strata-dsv41` 0.1.57](strata/) |
| Context served | 262,144 (1 M native) |
| Thinking | on by default; off via `reasoning_effort: "none"` or `enable_thinking: false` |

## Verdict

**A fast single stream for a 763 B model, and almost nothing more under load.** 111.8 output
tok/s for one client, decode a flat 110 tok/s even behind 64k of context, and every needle
to 250k. With eight slots and sixteen clients it reaches 182 tok/s while the cards sit at
20–30 %: the DeepSeek engine is built for one user at a time, unlike Strata's Qwen engine,
which reached 645 tok/s at eight clients on the same cards.

| | DeepSeek-V4.1 GSQ-RCO 2.25 bpw · Strata · four cards | [DeepSeek-V4.1 EXL3 3 bpw · vLLM · two cards](../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/README.md) |
|---|---|---|
| Single stream, thinking on | 111.8 tok/s, p50 1.95 s | **136.5 tok/s**, p50 1.19 s |
| Decode | 110 tok/s, flat | 114–128 tok/s |
| Prefill | 4,079 / 4,321 / 4,159 tok/s at 64k / 128k / 250k | **11,386 tok/s at 180k** |
| Needles | 3 of 3 at 250k | 3 of 3 at 960k |
| Output at C=16, thinking on | 182.4 tok/s | — (8 engine slots by default) |

**Twice the cards, a lower bit width, and still behind the two-card EXL3 setup on every
throughput column.** The EXL3 pack ships its own vLLM recipe with sm120 kernels compiled for
exactly two of these cards; Strata's DeepSeek path is a port of a single-GPU engine that
splits layers across cards and runs them one after another.

**The layer split has to be set by hand.** The engine's own placement put 1, 1, 13 and 25
layers on the four cards, left two of them nearly empty and spilled 284 experts to the CPU;
`DS4_SPLIT=10,10,10,10` puts every expert in VRAM and doubles the prefill — see
[the setup](strata/README.md#the-automatic-layer-split-and-how-to-override-it).

## Measurements

| Setup | Scenarios |
|---|---|
| [`strata/`](strata/) | [single](strata/scenarios/single-stream.md) · [concurrent](strata/scenarios/concurrent-load.md) · [reasoning cost](strata/scenarios/reasoning-cost.md) · [long context](strata/scenarios/long-context.md) |
