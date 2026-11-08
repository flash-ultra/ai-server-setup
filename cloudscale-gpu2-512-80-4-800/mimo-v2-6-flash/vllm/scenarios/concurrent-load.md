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

## Above 256 clients

Measured 2026-11-08 with the same server flags, levels 256 to 1024 (a documented deviation, for
the comparison with [DeepSeek-V4-Flash-0731](../../../deepseek-v4-flash-0731/vllm/scenarios/concurrent-load.md),
which keeps climbing there). `bench.py` now also prints the wall-clock time and concurrency ÷
mean latency.

<!-- protocol v1 · DEVIATION levels 256,384,512,768,1024 · otherwise as above -->

**Thinking on**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 53.67 | 3652.4 | 69028.5 | 4.90 s | 6.65 s | 100 % · 100 % · 99 % · 99 % |
| 384 | 64.08 | 4346.1 | 82389.4 | 6.22 s | 8.33 s | 98 % · 98 % · 98 % · 98 % |
| 512 | 73.20 | 4968.9 | 94126.5 | 7.34 s | 10.16 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 82.88 | 5606.9 | 106548.7 | 9.88 s | 13.54 s | 100 % · 100 % · 100 % · 100 % |
| 1024 | 91.30 | 6179.7 | 117383.1 | 12.36 s | 17.24 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 52.24 | 3,555 | 1.03× |
| 384 | 61.74 | 4,187 | 1.04× |
| 512 | 69.75 | 4,735 | 1.05× |
| 768 | 77.73 | 5,259 | 1.07× |
| 1024 | 82.85 | 5,608 | 1.10× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 44.7 s | 47.99 | 3265.6 | 5.03 s | 50.89 answers/s |
| 384 | 45.8 s | 55.97 | 3796.5 | 6.37 s | 60.29 answers/s |
| 512 | 46.7 s | 62.72 | 4257.3 | 7.52 s | 68.13 answers/s |
| 768 | 47.8 s | 69.42 | 4696.8 | 10.09 s | 76.11 answers/s |
| 1024 | 49.9 s | 73.24 | 4957.2 | 12.59 s | 81.30 answers/s |

**Thinking off**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 73.78 | 3505.0 | 93510.5 | 3.49 s | 4.94 s | 97 % · 98 % · 98 % · 99 % |
| 384 | 88.70 | 4163.9 | 112377.9 | 4.39 s | 6.23 s | 100 % · 100 % · 100 % · 100 % |
| 512 | 100.70 | 4688.7 | 127542.7 | 5.22 s | 7.24 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 111.80 | 5243.0 | 141639.0 | 7.27 s | 10.10 s | 100 % · 100 % · 100 % · 100 % |
| 1024 | 120.92 | 5673.2 | 153201.7 | 9.01 s | 12.91 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 73.35 | 3,485 | 1.01× |
| 384 | 87.47 | 4,106 | 1.01× |
| 512 | 98.08 | 4,567 | 1.03× |
| 768 | 105.64 | 4,954 | 1.06× |
| 1024 | 113.65 | 5,332 | 1.06× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 44.6 s | 66.14 | 3142.3 | 3.59 s | 71.28 answers/s |
| 384 | 44.6 s | 79.52 | 3732.8 | 4.52 s | 85.04 answers/s |
| 512 | 44.6 s | 90.31 | 4205.0 | 5.34 s | 95.90 answers/s |
| 768 | 46.7 s | 95.80 | 4492.6 | 7.34 s | 104.60 answers/s |
| 1024 | 48.8 s | 99.03 | 4646.1 | 9.19 s | 111.46 answers/s |

**It keeps climbing to 1,024 clients.** Over the real run time 3,555 tok/s at 256 in this rerun,
within 3 % of the first run, and **5,608 at 1,024** with 82.9 answers/s at a median of 12.4 s;
by mean latency 5,503. Without thinking 113.7 answers/s at 1,024. That is level with
DeepSeek-V4-Flash-0731 at TP=4 (5,956) and half of what the same DeepSeek delivers as
[four copies](../../../deepseek-v4-flash-0731/vllm/scenarios/data-parallel.md) (11,535).
