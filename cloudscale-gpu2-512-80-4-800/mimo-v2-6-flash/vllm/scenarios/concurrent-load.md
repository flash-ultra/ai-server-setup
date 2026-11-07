# Scenario: concurrent load — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4](../README.md) · `MiMo-V2.6-Flash-RL` · [the four-card machine](../../../README.md) · measured 2026-11-06, 16:58–17:12

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations: levels 1 to 256, 40 s
each, `max_tokens 512`, 3 warmup requests, tokens from `usage`, both thinking arms, plus
the mixed run at 32.

## Result, thinking on (default)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 2.08 | 139.3 | 2666.7 | 0.47 s | 0.61 s | 98 % × 4 |
| 8 | 6.95 | 465.2 | 8930.3 | 1.13 s | 1.50 s | 98–99 % |
| 16 | 9.65 | 660.6 | 12414.3 | 1.63 s | 2.33 s | 95–99 % |
| 32 | 13.95 | 949.2 | 17940.3 | 2.29 s | 3.13 s | 100 % × 4 |
| 64 | 19.45 | 1332.5 | 25022.6 | 3.33 s | 4.54 s | 100 % × 4 |
| 128 | 38.52 | 2597.7 | 49521.1 | 3.37 s | 4.60 s | 100 % × 4 |
| 256 | **54.98** | **3739.6** | 70699.2 | 4.77 s | 6.47 s | 100 % × 4 |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 2.08 | 139.3 | — |
| 8 | 6.95 | 465.2 | — |
| 16 | 9.65 | 660.6 | — |
| 32 | 13.95 | 949.2 | — |
| 64 | 19.22 | 1,317 | 1.01× |
| 128 | 37.98 | 2,561 | 1.01× |
| 256 | 53.67 | 3,650 | 1.02× |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 14.00 | 955.2 | 18007.2 | 2.29 s | 3.10 s |
| mixed | 2.23 | 969.6 | 2746.1 | 17.52 s | 22.16 s |

## Result, thinking off

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · chat_template_kwargs: {"enable_thinking": false} -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 2.80 | 138.3 | 3554.3 | 0.36 s | 0.47 s | 97–98 % |
| 8 | 9.53 | 450.2 | 12070.7 | 0.82 s | 1.15 s | 96–99 % |
| 16 | 14.07 | 652.7 | 17824.2 | 1.13 s | 1.55 s | 99 % × 4 |
| 32 | 19.77 | 922.1 | 25047.6 | 1.59 s | 2.26 s | 99–100 % |
| 64 | 26.60 | 1257.4 | 33709.4 | 2.42 s | 3.29 s | 100 % × 4 |
| 128 | 54.27 | 2538.2 | 68753.7 | 2.40 s | 3.32 s | 100 % × 4 |
| 256 | **75.58** | **3564.5** | 95766.0 | 3.44 s | 4.81 s | 100 % × 4 |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 2.78 | 137.2 | 1.01× |
| 8 | 9.53 | 450.2 | — |
| 16 | 14.07 | 652.7 | — |
| 32 | 19.77 | 922.1 | — |
| 64 | 26.45 | 1,250 | 1.01× |
| 128 | 53.33 | 2,494 | 1.02× |
| 256 | 74.42 | 3,510 | 1.02× |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 19.77 | 921.7 | 25047.2 | 1.60 s | 2.27 s |
| mixed | 2.85 | 1087.2 | 3480.4 | 16.78 s | 19.43 s |

## Reading it

**From 64 to 128 clients the answer rate doubles at unchanged latency**, in both arms
(19.2 → 38.0 and 26.5 → 53.3 over the real run time, p50 3.3 → 3.4 s and 2.4 → 2.4 s). The ladder below 128 is
not limited by the cards — they are at 100 % from 32 on — but by something that stops
binding at 128; the size of vLLM's captured CUDA graphs or the default batch budget are
the likely candidates. Untested. The two-card ladder rose smoothly through the same range.

**At 256 the ladder still has not turned over**, as on two cards: p50 under five seconds
with thinking on. Against the two-card machine at 256, over the real run time: 3,650 against
3,030 output tok/s, 53.7 against 44.6 answers/s — 1.20×. Against Qwen3.8-Flash-Next FP8 on
these cards: 3,650 against 1,989 tok/s and 54 against 10 answers/s, because Qwen thinks for 160 tokens
where MiMo thinks for 14.
