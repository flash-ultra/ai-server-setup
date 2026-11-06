# Scenario: reasoning cost — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4 EP, NVFP4](../README.md) · `GLM-5.3-Flash` · [the four-card machine](../../../README.md) · measured 2026-11-06, 18:29–18:35

## Method

Protocol [`v1`](../../../../benchmark/README.md), `--scenario reasoning --thinking-key enable_thinking`.
The key is known to be ignored by this model ([pinned values](../README.md#pinned-values));
the row is kept as the evidence.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|---|
| 8 | default (max) | 1.15 | 413.3 | 359 | 83 % | 358 | 7.19 s |
| 8 | `reasoning_effort=low` | **3.17** | 164.7 | **52** | **2 %** | 301 | **2.53 s** |
| 8 | `enable_thinking: false` (ignored) | 1.15 | 403.2 | 351 | 81 % | 378 | 7.36 s |
| 32 | default (max) | 2.10 | 745.3 | 355 | 83 % | 348 | 17.00 s |
| 32 | `reasoning_effort=low` | **4.12** | 210.2 | **51** | **4 %** | 291 | **7.89 s** |
| 32 | `enable_thinking: false` (ignored) | 2.00 | 738.9 | 369 | 85 % | 333 | 17.38 s |

**`low` is GLM's off switch in all but name**: 52 tokens, 2–4 % thinking, 2.8× the answers
at C=8 and 2.0× at C=32. The output-token rate falls with it — at 52 tokens per answer the
1,300-token prompt is most of each request's work. The `enable_thinking` rows match the
default within noise, confirming the key does nothing.
