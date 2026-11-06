# Scenario: quality (`q1`) — Strata DeepSeek engine, two replicas

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), both thinking arms.

**Setup:** [Strata 0.2.11, `strata-dsv41`, `--replicas 2`, `DS4_SPLIT=20,20`](../README.md#two-engines-instead-of-one) · `DeepSeek-V4.1-Flash-1017` GSQ-RCO 2.25 bpw · [the four-card machine](../../../README.md) · measured 2026-11-06, 21:29–23:04

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-tokens 50000 -M client_timeout=3600`, **`--max-connections 16`**
(two engines with eight slots each). Thinking off is `--reasoning-effort none`, verified
(21 → 2 completion tokens). HumanEval in Inspect's Docker sandbox. **Every sample of every
cell finished with `stop`**; no answer reached the cap.

## Result

| Benchmark | thinking **off** | thinking **on** |
|---|---|---|
| GSM8K | 0.965 ± 0.013 | 0.970 ± 0.012 |
| IFEval `prompt_strict` | 0.830 ± 0.027 | **0.965** ± 0.013 |
| IFEval `inst_strict` | 0.884 | **0.978** |
| MMLU-Pro | 0.805 ± 0.028 | **0.890** ± 0.022 |
| HumanEval | 0.945 ± 0.018 | **0.994** ± 0.006 |

## Against every model on the same cards

| Thinking on | DeepSeek-V4.1 2.25 bpw · Strata | [Qwen3.8-Flash-Next](../../../qwen3-8-flash-next/) FP8 · vLLM | Qwen Q8_0 · Strata | [GLM-5.3-Flash](../../../glm-5-3-flash/) NVFP4 · max | [MiMo-V2.6-Flash](../../../mimo-v2-6-flash/) FP8 |
|---|---|---|---|---|---|
| GSM8K | 0.970 | **0.990** | 0.975 | 0.985 | 0.975 |
| IFEval prompt_strict | **0.965** | 0.930 | 0.945 | 0.880 | 0.850 |
| MMLU-Pro | **0.890** | 0.860 † | 0.875 | 0.870 | 0.850 ‡ |
| HumanEval | **0.994** | 0.976 | 0.982 | 0.970 | 0.963 |

† two at the cap · ‡ six at a 32,768 cap

| Thinking off | DeepSeek | Qwen FP8 | Qwen Q8_0 | GLM (low) | MiMo |
|---|---|---|---|---|---|
| GSM8K | 0.965 | 0.980 | **0.985** | **0.985** | 0.945 |
| IFEval prompt_strict | 0.830 | 0.825 | **0.845** | 0.810 | 0.840 |
| MMLU-Pro | 0.805 | **0.885** | 0.875 | 0.815 | 0.775 |
| HumanEval | 0.945 | 0.939 | **0.957** | 0.939 | 0.933 |

**With thinking, the best model measured on this machine, at 2.25 bits per weight.** First or
level-first in three of four benchmarks, and the IFEval and HumanEval leads (0.965 against
0.945, 0.994 against 0.982) clear one standard error. Without thinking it sits in the middle
and trails both 8-bit Qwen checkpoints by eight points on MMLU-Pro — the same pattern the
3-bit Qwen pack showed: a low bit width costs stored knowledge, and thinking pays it back.
