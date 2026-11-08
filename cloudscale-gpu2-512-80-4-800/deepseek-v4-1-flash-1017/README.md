# DeepSeek-V4.1-Flash-1017 · EXL3 3 bpw and GSQ-RCO 2.25 bpw

DeepSeek's 763 B mixture-of-experts on all four cards of [this machine](../README.md),
measured 2026-11-06 and 07. The official FP8 checkpoint is 510 GB and does not fit 382 GiB,
so two quantised packs: the **EXL3 3-bit pack** with its own vLLM recipe, the one
[measured on the two-card machine](../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/README.md),
here with its four-card profile; and **ISTA-DASLab's 2.25-bit GSQ-RCO set** under Strata's
DeepSeek engine.

## Verdict, EXL3 on four cards

**The best DeepSeek setup measured, and the fastest single stream of the vLLM setups on this
machine.** 153 tok/s single stream, 467 / 673 tok/s at C=8 / 16 and **1,510 tok/s at C=256**,
three quarters of Qwen3.8-Flash-Next under vLLM (1,989) — with every expert in VRAM, a 4.5 M-token KV pool, and a
million-token prompt read in 88 s with every needle found. `q1` on these cards
reproduces the two-card run: MMLU-Pro 0.850, IFEval 0.955, **HumanEval 0.994** with thinking
([quality](vllm-exl3/scenarios/quality.md)). All of it on
NCCL, because this VM lacks the peer atomics the pack's own all-reduce kernels need
([setup](vllm-exl3/README.md#one-switch-this-machine-needs-no-p2p-atomics)).

| | EXL3 3 bpw · 4 cards | EXL3 3 bpw · 2 cards | GSQ-RCO 2.25 bpw · Strata · 4 cards |
|---|---|---|---|
| Single stream, thinking on | **153.2 tok/s** | 136.5 | 111.8 |
| C=8 / C=16 | **467 / 673 tok/s** | 261 / 254 | 151 / 154 (one engine), 302 / 282 (two) |
| C=256 | **1,510 tok/s, 9.2 answers/s** | 399 | — |
| Prefill 250k | **13,264 tok/s** | 11,386 (180k) | 4,159 |
| Needles | 3 of 3 at **960k** | 3 of 3 at 960k | 3 of 3 at 250k |
| `q1` thinking on: MMLU-Pro / IFEval / HumanEval | 0.850 / 0.955 / **0.994** | 0.880 / 0.955 / **1.000** | **0.890 / 0.965** / **0.994** |

**Four cards scale this pack where they did not scale MiMo**: 1.8–3.8× the two-card
throughput under load, against 1.2×, because the two-card setup runs at most 32 sequences
and keeps part of the experts in host RAM, while four cards hold all of them and admit 128.

## Verdict, GSQ-RCO under Strata

| | |
|---|---|
| Checkpoint | [`ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF`](https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF) IQ2_XS, **2.25 bpw** — 155 GB of model, a 111 GB Engram n-gram table (IQ4_NL) and the 8 GB DSpark drafter |
| Base | [`deepseek-ai/DeepSeek-V4.1-Flash-1017`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), 763 B total, 384 routed experts, 6 active, 40 layers |
| Setup | [Strata 0.2.11 with its DeepSeek engine `strata-dsv41` 0.1.57](strata/) |
| Context served | 262,144 (1 M native) |
| Thinking | on by default; off via `reasoning_effort: "none"` or `enable_thinking: false` |

**A fast single stream for a 763 B model, and almost nothing more under load.** 111.8 output
tok/s for one client, decode a flat 110 tok/s even behind 64k of context, and every needle
to 250k. With eight slots it levels off at about 154 tok/s from four clients on, while the cards sit
at 20–30 %: the DeepSeek engine is built for one user at a time, unlike Strata's Qwen engine,
which reached 645 tok/s at eight clients on the same cards.

| | DeepSeek-V4.1 GSQ-RCO 2.25 bpw · Strata · four cards | [DeepSeek-V4.1 EXL3 3 bpw · vLLM · two cards](../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/README.md) |
|---|---|---|
| Single stream, thinking on | 111.8 tok/s, p50 1.95 s | **136.5 tok/s**, p50 1.19 s |
| Decode | 110 tok/s, flat | 114–128 tok/s |
| Prefill | 4,079 / 4,321 / 4,159 tok/s at 64k / 128k / 250k | **11,386 tok/s at 180k** |
| Needles | 3 of 3 at 250k | 3 of 3 at 960k |
| Output at C=16, thinking on | 153.7 tok/s | — (8 engine slots by default) |

**Behind the EXL3 pack on every throughput column**, on two cards as on four: Strata's
DeepSeek path is a port of a single-GPU engine that splits layers across cards and runs
them one after another, where the pack's recipe runs TP and EP with batched kernels.

**Two engines on two cards each double that**: `--replicas 2` reaches 302 tok/s at C=8 and
holds about 290 above it, the cards at 50 % — a third of what vLLM serves with MiMo at C=32
on these cards, and the configuration to use for more than one user.

**The layer split has to be set by hand.** The engine's own placement put 1, 1, 13 and 25
layers on the four cards, left two of them nearly empty and spilled 284 experts to the CPU;
`DS4_SPLIT=10,10,10,10` puts every expert in VRAM and doubles the prefill — see
[the setup](strata/README.md#the-automatic-layer-split-and-how-to-override-it).

**And the best answers on this machine, with thinking.** Under `q1` it leads IFEval (0.965),
MMLU-Pro (0.890) and HumanEval (0.994, 163 of 164) and every answer stopped on its own;
without thinking it falls to the middle of the field, 8 points behind the 8-bit Qwen
checkpoints on MMLU-Pro — [quality](strata/scenarios/quality.md).

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm-exl3/`](vllm-exl3/) | [single](vllm-exl3/scenarios/single-stream.md) · [concurrent](vllm-exl3/scenarios/concurrent-load.md) · [reasoning cost](vllm-exl3/scenarios/reasoning-cost.md) · [long context](vllm-exl3/scenarios/long-context.md) · [quality](vllm-exl3/scenarios/quality.md) |
| [`strata/`](strata/) | [single](strata/scenarios/single-stream.md) · [concurrent](strata/scenarios/concurrent-load.md) · [reasoning cost](strata/scenarios/reasoning-cost.md) · [long context](strata/scenarios/long-context.md) · [quality](strata/scenarios/quality.md) |
