# Scenario: concurrent load — Strata IQ3_S, four cards, 8 slots

The ladder at 1 / 4 / 8 / 16 clients, both thinking arms, plus the mixed-traffic run at 32.

**Setup:** [Strata 0.2.11, IQ3_S, layer split over four cards, `--parallel 8`](../README.md) ·
[the four-card machine](../../../README.md) · measured 2026-11-06, 12:08–12:18

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md) with one
**deviation: levels 1, 4, 8, 16 instead of the pinned 1 … 256.** Strata serves at most
eight requests at once (`--parallel` caps at 8), so every level above 8 measures the queue,
and the protocol ladder's top would be forty seconds of waiting. Everything else pinned:
`max_tokens 512`, 40 s per level, 3 warmup requests, tokens from `usage`.

## Result, thinking on (default)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · DEVIATION: levels 1,4,8,16 instead of the pinned 1,8,16,32,64,128,256 -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 1.18 | 228.7 | 1712.7 | 0.85 s | 1.10 s | 20 · 20 · 20 · 32 % |
| 4 | 2.05 | 441.7 | 3030.8 | 2.02 s | 2.84 s | 68 · 63 · 66 · 82 % |
| 8 | 3.12 | **645.5** | 4592.4 | 2.48 s | 3.88 s | 63 · 66 · 67 · 79 % |
| 16 | 3.33 | 722.1 | 4921.6 | 4.70 s | 9.47 s | 70 · 66 · 67 · 82 % |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 3.67 | 777.1 | 5418.6 | 8.17 s | 19.77 s |
| mixed | 2.08 | 992.6 | 2670.8 | 16.89 s | 43.13 s |

## Result, thinking off

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · chat_template_kwargs: {"enable_thinking": false} · DEVIATION: levels 1,4,8,16 -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 3.50 | 182.6 | 4463.1 | 0.29 s | 0.39 s | 20 · 20 · 20 · 31 % |
| 4 | 6.10 | 314.4 | 7774.7 | 0.64 s | 0.88 s | 52 · 51 · 52 · 60 % |
| 8 | 7.97 | 405.2 | 10158.6 | 0.98 s | 1.34 s | 48 · 39 · 41 · 53 % |
| 16 | 8.40 | 428.9 | 10702.0 | 1.63 s | 3.88 s | 46 · 48 · 47 · 57 % |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 8.45 | 434.9 | 10769.2 | 2.97 s | 9.71 s |
| mixed | 2.23 | 909.4 | 2690.2 | 15.33 s | 39.85 s |

## The Q8_0 pack, same engine

<!-- protocol v1 · DEVIATION: levels 1,4,8,16 -->

| Output tok/s | C=1 | C=4 | C=8 | C=16 | C=32 uniform | C=32 mixed |
|---|---|---|---|---|---|---|
| Q8_0, thinking on | 187.8 | 377.4 | **564.2** | 582.7 | 668.8 | 873.2 |
| Q8_0, thinking off | 151.5 | 272.6 | 345.6 | 350.9 | 378.6 | 823.4 |
| Q8_0, answers/s on / off | 0.95 / 3.00 | 1.82 / 5.45 | 2.70 / 6.80 | 3.00 / 6.97 | 3.27 / 7.55 | 1.80 / 2.02 |
| Q8_0, p50 on / off | 1.00 / 0.32 s | 2.23 / 0.72 s | 2.91 / 1.18 s | 5.26 / 2.08 s | 9.23 / 3.52 s | 21.8 / 17.8 s |

Cards at 66–86 % from C=4 on, 13–15 % under the 3-bit pack at every level, the same
slot-limit knee between 8 and 16.

## Reading it, against vLLM on the same cards

| Output tok/s, thinking on | C=1 | C=4 | C=8 | C=16 | C=32 uniform | C=256 |
|---|---|---|---|---|---|---|
| **Strata IQ3_S, 8 slots** | **228.7** | **441.7** | **645.5** | 722.1 (queue) | 777.1 (queue) | — |
| Strata Q8_0, 8 slots | 187.8 | 377.4 | 564.2 | 582.7 (queue) | 668.8 (queue) | — |
| vLLM FP8 TP=4 + MTP draft | 174.0 | — | 517.3 | 722.0 | 979.5 | 2235.2 |
| vLLM FP8 TP=4 | 110.3 | — | 446.6 | 654.2 | 893.5 | 2274.9 |
| Strata IQ3_S, Rocky 2× RTX PRO 4500, 8 slots | 141.4 | — | 346.0 | 391.0 | queue | — |

**Up to eight clients Strata is the faster server on these cards; at sixteen the two are
level; beyond that only vLLM scales.** The crossover is exactly the slot limit: from C=8
to C=16 Strata adds 12 % and doubles p50, because the ninth client waits. The cards never
pass 82 % under Strata, so the ceiling is the engine's eight-slot batch, not the GPUs. The
mixed run tells the same story harder: p95 of 43 s at C=32, because long prompts hold a
slot while thirty-one others queue.
