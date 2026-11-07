# Scenario: quality (`q1`) — Hy3, TP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), at `reasoning_effort`
`high` and `no_think`.

**Setup:** [vLLM 0.33.0 TP=4, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 21:07–22:48

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox. The thinking arm runs at the server default
`reasoning_effort: high`; the off arm sends `chat_template_kwargs: {reasoning_effort: "no_think"}`
([pinned values](../README.md#pinned-values)). Every sample of every cell finished with `stop`.
The thinking arm took 95 minutes, the off arm 6.

## Result

| Benchmark | `no_think` | `high` (server default) |
|---|---|---|
| GSM8K | 0.965 ± 0.013 | **0.980** ± 0.010 |
| IFEval `prompt_strict` | 0.880 ± 0.023 | **0.940** ± 0.017 |
| IFEval `inst_strict` | 0.921 | **0.962** |
| MMLU-Pro | 0.795 ± 0.029 | **0.880** ± 0.023 |
| HumanEval | 0.921 ± 0.021 | **0.994** ± 0.006 |
| Median output tokens, GSM8K / MMLU-Pro | 106 / 274 | 1,129 / 2,871 |

**Thinking pays on knowledge and code, and costs ten times the tokens.** MMLU-Pro rises by
8.5 points and HumanEval by 7.3, both beyond two standard errors; GSM8K was already high
without it. The longest MMLU-Pro answer took 43,253 tokens, still inside the 50,000 cap.

## Against the other models on the same cards

| Thinking on (default) | Hy3 FP8 | DeepSeek-V4.1 | Beam-1.0 NVFP4 | Qwen3.8-Flash-Next FP8 | GLM-5.3-Flash NVFP4 | Nemotron-3-Super NVFP4 |
|---|---|---|---|---|---|---|
| GSM8K | 0.980 | 0.970 | 0.955 | **0.990** | 0.985 | 0.970 |
| IFEval prompt_strict | 0.940 | **0.965** ¹ | 0.910 | 0.930 | 0.880 | 0.910 |
| MMLU-Pro | 0.880 | **0.890** ¹ | **0.890** | 0.860 | 0.870 | 0.830 |
| HumanEval | **0.994** | **0.994** ¹ | 0.951 | 0.976 | 0.970 | 0.982 |

¹ the GSQ-RCO 2.25 bpw set under Strata on these cards.

**Level with DeepSeek:** no difference to it reaches two standard errors, the largest being
IFEval at 2.5 points. Against Beam only HumanEval separates (0.994 against 0.951).
