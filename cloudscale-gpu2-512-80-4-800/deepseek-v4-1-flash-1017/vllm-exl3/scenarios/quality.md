# Scenario: quality (`q1`) — DeepSeek-V4.1 EXL3 3 bpw, four cards

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), thinking on and off.

**Setup:** [vLLM + EXL3, the pack's recipe, `PROFILE=8x REPLICA=0`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-08, 09:15–09:43

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox, against the engine with the pack's API key. Thinking off
via `chat_template_kwargs: {enable_thinking: false}`: the switch question returns 19 reasoning
tokens by default and 0 with it, and `thinking: false` does the same. Every sample of every cell
finished with `stop`; the longest MMLU-Pro answer took 49,431 tokens. The thinking arm took 24
minutes, the off arm 4.

## Result

| Benchmark | thinking **off** | thinking **on** | same pack, two cards, on |
|---|---|---|---|
| GSM8K | **0.975** ± 0.011 | 0.970 ± 0.012 | 0.970 |
| IFEval `prompt_strict` | 0.860 ± 0.025 | **0.955** ± 0.015 | 0.955 |
| IFEval `inst_strict` | 0.906 | **0.969** | 0.969 |
| MMLU-Pro | **0.880** ± 0.023 | 0.850 ± 0.025 | 0.880 |
| HumanEval | 0.945 ± 0.018 | **0.994** ± 0.006 | 1.000 |
| Median output tokens, GSM8K / MMLU-Pro | 124 / 144 | 178 / 418 | — |

**The four-card profile reproduces the [two-card run](../../../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/vllm-exl3/scenarios/quality.md):**
IFEval identical to the third decimal, GSM8K equal, MMLU-Pro and HumanEval within about one
standard error.

**Thinking pays on instructions and code, not on knowledge:** IFEval gains 9.5 points and
HumanEval 4.9, both beyond two standard errors. MMLU-Pro is 3 points better without thinking,
inside the noise.

## Against the other models on the same cards

| Thinking on | DeepSeek-V4.1 EXL3 | DeepSeek-V4.1 GSQ-RCO · Strata | DeepSeek-V4-Flash-0731 | Hy3 FP8 | Beam-1.0 NVFP4 | Qwen3.8-Flash-Next FP8 |
|---|---|---|---|---|---|---|
| GSM8K | 0.970 | 0.970 | 0.965 | 0.980 | 0.955 | **0.990** |
| IFEval prompt_strict | 0.955 | **0.965** | 0.925 | 0.940 | 0.910 | 0.930 |
| MMLU-Pro | 0.850 | **0.890** | 0.870 | 0.880 | **0.890** | 0.860 |
| HumanEval | **0.994** | **0.994** | 0.970 | **0.994** | 0.951 | 0.976 |

**The pack sits in the top group, not ahead of it:** none of its values is two standard errors
below the best in its row.
