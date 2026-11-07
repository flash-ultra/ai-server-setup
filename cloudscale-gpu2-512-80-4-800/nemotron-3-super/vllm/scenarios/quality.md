# Scenario: quality (`q1`) — Nemotron-3-Super, DP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), both thinking arms.

**Setup:** [vLLM 0.33.0, four copies](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 18:19–19:23

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox. **Thinking off is `--extra-body
'{"chat_template_kwargs":{"enable_thinking":false}}'`**: this model ignores `reasoning_effort`.
The logs confirm the switch took — the off arm reports 0 reasoning tokens on every
MMLU-Pro sample.

## Result

| Benchmark | thinking **off** | thinking **on** | Stop reasons |
|---|---|---|---|
| GSM8K | 0.975 ± 0.011 | 0.970 ± 0.012 | 200 / 200 `stop` both |
| IFEval `prompt_strict` | 0.795 ± 0.029 | **0.910** ± 0.020 | 1 at the 50,000 cap in each arm |
| IFEval `inst_strict` | 0.858 | **0.937** | |
| MMLU-Pro | **0.860** ± 0.025 | 0.830 ± 0.027 | **off: 5 at the cap; on: 3 at the cap** |
| HumanEval | 0.927 ± 0.020 | **0.982** ± 0.010 | 164 / 164 `stop` both |

**Thinking off does not stop the model from reasoning; it moves the reasoning into the
answer.** MMLU-Pro answers with thinking off have a median of 921 tokens against 1,719 with
thinking on, and 11 of 200 run past 20,000 tokens (8 with thinking on). That is why MMLU-Pro
reads higher without thinking, and why both arms carry truncated answers: some of the long
ones are loops that the cap cuts off. Both MMLU-Pro figures are floors — at most 0.885 off
and 0.845 on if every truncated answer had been right.

## Against the other models on the same cards

| Thinking on | Nemotron-3-Super NVFP4 | Qwen3.8-Flash-Next FP8 | DeepSeek-V4.1 (Strata 2.25 bpw) | MiMo-V2.6-Flash | GLM-5.3-Flash (max) |
|---|---|---|---|---|---|
| GSM8K | 0.970 | **0.990** | 0.970 | 0.975 | 0.985 |
| IFEval prompt_strict | 0.910 | 0.930 | **0.965** | 0.850 | 0.880 |
| MMLU-Pro | 0.830 ‡ | 0.860 † | **0.890** | 0.850 | 0.870 |
| HumanEval | 0.982 | 0.976 | **0.994** | 0.963 | 0.970 |

‡ three at the cap · † two at the cap

**Level with Qwen3.8-Flash-Next on arithmetic, code and instruction following, three points
behind on knowledge** — from 12 B active parameters on one card per copy.
