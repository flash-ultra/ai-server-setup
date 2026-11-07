# Scenario: quality (`q1`) — Beam-1.0, TP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), at `reasoning_effort`
minimal and at the default (max).

**Setup:** [vLLM 0.33.0 TP=4, NVFP4](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 19:51–20:21

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox. **Deviation: the thinking-off arm is replaced by
`--reasoning-effort minimal`** (budget 8), because the model has no off switch
([pinned values](../README.md#pinned-values)). The setting reaches the model: on GSM8K the
minimal arm's answers have a median of 227 tokens, 121 of them thinking. Every sample of
every cell finished with `stop`; both arms together took 30 minutes.

## Result

| Benchmark | effort **minimal** | effort **max** (default) |
|---|---|---|
| GSM8K | **0.970** ± 0.012 | 0.955 ± 0.015 |
| IFEval `prompt_strict` | 0.890 ± 0.022 | **0.910** ± 0.020 |
| IFEval `inst_strict` | 0.928 | **0.943** |
| MMLU-Pro | 0.870 ± 0.024 | **0.890** ± 0.022 |
| HumanEval | 0.951 ± 0.017 | 0.951 ± 0.017 |

**The smallest budget costs almost nothing**: every cell within one standard error of the
default, GSM8K slightly ahead. What the card claims — answers of leading quality with few
reasoning tokens — holds here as far as 200 samples per benchmark can see.

## Against the other models on the same cards

| Thinking on (default) | Beam-1.0 NVFP4 | DeepSeek-V4.1 | Qwen3.8-Flash-Next FP8 | GLM-5.3-Flash NVFP4 | Nemotron-3-Super NVFP4 |
|---|---|---|---|---|---|
| GSM8K | 0.955 | 0.970 | **0.990** | 0.985 | 0.970 |
| IFEval prompt_strict | 0.910 | **0.965** ¹ | 0.930 | 0.880 | 0.910 |
| MMLU-Pro | **0.890** | **0.890** ¹ | 0.860 | 0.870 | 0.830 |
| HumanEval | 0.951 | **0.994** ¹ | 0.976 | 0.970 | 0.982 |

¹ the GSQ-RCO 2.25 bpw set under Strata on these cards; the EXL3 pack on two cards measured
0.955 / 0.880 / 1.000.

**Level with DeepSeek on knowledge, behind it on instructions and code.** HumanEval 0.951 is
the lowest thinking-on score in this table; 8 of 164 tasks fail in both arms.
