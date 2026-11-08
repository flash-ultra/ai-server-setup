# Scenario: quality (`q1`) — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), thinking on and off.

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md), no draft model · [the four-card machine](../../../README.md) · measured 2026-11-08, 00:13–01:08

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox. The thinking arm runs at the server default
`thinking: true`; the off arm sends `chat_template_kwargs: {thinking: false}`
([pinned values](../README.md#pinned-values)). Every sample of every cell finished with `stop`;
the longest MMLU-Pro answer took 49,374 tokens, just inside the cap. The thinking arm took 49
minutes, the off arm 6.

## Result

| Benchmark | thinking **off** | thinking **on** | two cards, SGLang, off / on |
|---|---|---|---|
| GSM8K | **0.980** ± 0.010 | 0.965 ± 0.013 | 0.985 / 0.970 |
| IFEval `prompt_strict` | 0.840 ± 0.026 | **0.925** ± 0.019 | 0.810 / 0.895 |
| IFEval `inst_strict` | 0.896 | **0.953** | 0.874 / 0.928 |
| MMLU-Pro | 0.790 ± 0.029 | **0.870** ± 0.024 | 0.845 / 0.870 |
| HumanEval | 0.909 ± 0.023 | **0.970** ± 0.013 | 0.939 / 0.963 |
| Median output tokens, GSM8K / MMLU-Pro | 93 / 106 | 218 / 430 | — |

**Thinking buys instructions, knowledge and code; arithmetic was already there.** IFEval rises by
8.5 points and MMLU-Pro by 8, both beyond two standard errors; GSM8K is a little better without
it, as on the [two-card machine](../../../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-flash-0731/sglang/scenarios/quality.md).
The two engines agree within two standard errors in every cell; with thinking, MMLU-Pro is
identical.

**It thinks briefly:** a median of 430 tokens per MMLU-Pro answer, against 2,871 for
[Hy3](../../../hy3/vllm/scenarios/quality.md) at a score one point higher.

## Against the other models on the same cards

| Thinking on | DeepSeek-V4-Flash-0731 | DeepSeek-V4.1 | Hy3 FP8 | Beam-1.0 NVFP4 | Qwen3.8-Flash-Next FP8 |
|---|---|---|---|---|---|
| GSM8K | 0.965 | 0.970 | 0.980 | 0.955 | **0.990** |
| IFEval prompt_strict | 0.925 | **0.965** ¹ | 0.940 | 0.910 | 0.930 |
| MMLU-Pro | 0.870 | **0.890** ¹ | 0.880 | **0.890** | 0.860 |
| HumanEval | 0.970 | **0.994** ¹ | **0.994** | 0.951 | 0.976 |

¹ the GSQ-RCO 2.25 bpw set under Strata on these cards.

**The older release sits just below V4.1 on every benchmark**, no difference reaching two
standard errors.
