# Scenario: vision (`vq1`) — DeepSeek-V4.1 EXL3 3 bpw, four cards

MMMU, MathVista and DocVQA at 200 samples each, thinking on and off.

**Setup:** [vLLM + EXL3, the pack's recipe, `PROFILE=8x REPLICA=0`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-08, 13:36–14:31

## Method

Protocol [`vq1`](../../../../benchmark/README.md#vision-protocol-vq1-measured-with-inspect-ai). The
pack loads the 32-layer vision encoder (0.77 GiB, bf16) by default and budgets 1,024 tokens per
image; a 256 × 256 test image cost 234 prompt tokens and came back described correctly. Thinking
off via `enable_thinking: false`. The 200 samples per benchmark are the same as for
[Qwen3.8-Flash-Next](../../../qwen3-8-flash-next/vllm/scenarios/vision.md), checked by sample ID.

## Result

| Benchmark | thinking **off** | thinking **on** | time on / off |
|---|---|---|---|
| MMMU (multiple choice) | 0.755 ± 0.030 | **0.795** ± 0.029 | 15 / 8 min |
| MathVista | 0.765 ± 0.030 | **0.825** ± 0.027 | 14 / 2 min |
| DocVQA (ANLS) | **0.891** ± 0.021 | 0.838 ± 0.024 | 6 / 0.6 min |
| Median output tokens, MMMU / MathVista / DocVQA | 108 / 150 / 51 | 303 / 451 / 100 | |

**15 MMMU answers with thinking and 9 without ran into the 50,000-token cap**, in Music,
Mechanical Engineering, Materials and Math. They are not repetition loops: the model keeps
weighing the options ("Is it possible the question is from a source where …") and never
commits. They count as wrong. Thinking moves MMMU and MathVista up by 4 and 6 points and DocVQA
down by 5; none of the three reaches two standard errors.

## Against Qwen3.8-Flash-Next on the same samples

| Thinking on / off | DeepSeek-V4.1 EXL3 3 bpw | Qwen3.8-Flash-Next FP8 |
|---|---|---|
| MMMU (multiple choice) | 0.795 / **0.755** | **0.865** / 0.725 |
| MathVista | 0.825 / **0.765** | **0.890** / 0.745 |
| DocVQA (ANLS) | 0.838 / 0.891 | **0.955** / **0.893** |
| Prompt tokens for a 256 × 256 test image | 234 | 137 |
| MMMU answers at the 50,000-token cap | 15 / 9 | 1 / 0 |
| Median output tokens, MMMU, thinking off | 108 | 5 |

**With thinking Qwen reads images better:** 7, 6.5 and 11.7 points ahead, the DocVQA gap beyond
four standard errors, the other two just under two. **Without thinking the two are level**, with
DeepSeek 2–3 points ahead on MMMU and MathVista; Qwen then answers in a handful of tokens, while
DeepSeek still reasons in the visible text.
