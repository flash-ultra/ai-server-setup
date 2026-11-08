# Scenario: vision (`vq1`) — Qwen3.8-Flash-Next FP8, TP=4

MMMU, MathVista and DocVQA at 200 samples each, thinking on and off.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md), the flags of the text runs · [the four-card machine](../../../README.md) · measured 2026-11-08, 14:38–15:15

## Method

Protocol [`vq1`](../../../../benchmark/README.md#vision-protocol-vq1-measured-with-inspect-ai). vLLM
0.33 admits up to 999 images per prompt by default; a 256 × 256 test image cost 137 prompt tokens
and came back described correctly. Thinking off via `enable_thinking: false`. The 200 samples
per benchmark are the same as for
[DeepSeek-V4.1 EXL3](../../../deepseek-v4-1-flash-1017/vllm-exl3/scenarios/vision.md), checked by
sample ID.

## Result

| Benchmark | thinking **off** | thinking **on** | time on / off |
|---|---|---|---|
| MMMU (multiple choice) | 0.725 ± 0.032 | **0.865** ± 0.024 | 16 / 3 min |
| MathVista | 0.745 ± 0.031 | **0.890** ± 0.022 | 11 / 2 min |
| DocVQA (ANLS) | 0.893 ± 0.021 | **0.955** ± 0.013 | 2 / 0.6 min |
| Median output tokens, MMMU / MathVista / DocVQA | 5 / 6 / 8 | 530 / 466 / 87 | |

**Thinking is worth 14 points on MMMU and MathVista and 6 on DocVQA**, each beyond two standard
errors. Without it the model answers straight away, in a median of five tokens. One MMMU answer
with thinking reached the 50,000-token cap.

## Against DeepSeek-V4.1 on the same samples

| Thinking on / off | DeepSeek-V4.1 EXL3 3 bpw | Qwen3.8-Flash-Next FP8 |
|---|---|---|
| MMMU (multiple choice) | 0.795 / **0.755** | **0.865** / 0.725 |
| MathVista | 0.825 / **0.765** | **0.890** / 0.745 |
| DocVQA (ANLS) | 0.838 / 0.891 | **0.955** / **0.893** |
| Prompt tokens for a 256 × 256 test image | 234 | 137 |
| MMMU answers at the 50,000-token cap | 15 / 9 | 1 / 0 |
| Median output tokens, MMMU, thinking off | 108 | 5 |

**With thinking Qwen reads images better:** 7, 6.5 and 11.7 points ahead, the DocVQA gap beyond
four standard errors, the other two just under two. **Without thinking the two are level.**
