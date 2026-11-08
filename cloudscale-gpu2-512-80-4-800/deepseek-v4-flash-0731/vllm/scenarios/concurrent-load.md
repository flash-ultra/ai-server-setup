# Scenario: concurrent load — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 23:50 – 2026-11-08, 02:19

Protocol [`v1`](../../../../benchmark/README.md), full ladder, both arms, no speculative
decoding; [DSpark](dspark.md) separately. **Deviation:** levels 384, 512, 768 and 1024 on top,
for the comparison with the August [configuration sweep](../../sglang/scenarios/concurrent-load.md#configuration-sweep-protocol-v1).
vLLM admits 1,024 sequences by default on 96 GB cards, so none of these levels queue in front
of the engine. Each ladder carries three readings of the same requests: `v1` over the 40 s
window, the estimate over the real run time that every other page uses
([why](../../../../benchmark/README.md#the-window-overstates-slow-answers)), and — new from this
run — the wall-clock time and concurrency ÷ mean latency.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

**Thinking on (server default `thinking: true`)**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.42 | 93.3 | 642.9 | 2.03 s | 4.19 s | 99 % · 99 % · 99 % · 99 % |
| 8 | 1.95 | 448.9 | 2970.2 | 3.96 s | 8.21 s | 100 % · 100 % · 100 % · 100 % |
| 16 | 3.77 | 694.0 | 5575.1 | 4.27 s | 7.21 s | 100 % · 100 % · 100 % · 100 % |
| 32 | 5.55 | 1026.0 | 8202.1 | 5.31 s | 12.29 s | 100 % · 100 % · 100 % · 100 % |
| 64 | 7.10 | 1507.2 | 10687.5 | 8.87 s | 17.99 s | 100 % · 100 % · 100 % · 100 % |
| 128 | 14.28 | 2846.8 | 21304.4 | 8.99 s | 18.28 s | 100 % · 98 % · 98 % · 98 % |
| 256 | 19.23 | 3955.2 | 28813.1 | 13.61 s | 28.07 s | 95 % · 94 % · 95 % · 94 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.42 | 93.3 | — |
| 8 | 1.95 | 448.9 | — |
| 16 | 3.75 | 689.8 | 1.01× |
| 32 | 5.55 | 1,026 | — |
| 64 | 7.10 | 1,507 | — |
| 128 | 14.24 | 2,838 | — |
| 256 | 18.81 | 3,869 | 1.02× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 41.3 s | 0.41 | 90.4 | 2.42 s | 0.41 answers/s |
| 8 | 45.6 s | 1.71 | 393.6 | 4.40 s | 1.82 answers/s |
| 16 | 45.7 s | 3.30 | 607.5 | 4.48 s | 3.57 answers/s |
| 32 | 46.8 s | 4.74 | 876.7 | 6.15 s | 5.20 answers/s |
| 64 | 49.0 s | 5.80 | 1231.4 | 9.92 s | 6.45 answers/s |
| 128 | 53.2 s | 10.73 | 2140.3 | 10.18 s | 12.57 answers/s |
| 256 | 57.4 s | 13.40 | 2756.0 | 15.43 s | 16.59 answers/s |

**Prompt mix at concurrency 32:** uniform 5.55 answers/s, 1,021.5 tok/s, p50 5.30 s · mixed 2.35 answers/s, 982.8 tok/s, p50 17.87 s.

**Thinking off (`thinking: false`)**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 2.20 | 81.0 | 2751.8 | 0.45 s | 0.57 s | 98 % · 99 % · 98 % · 98 % |
| 8 | 8.12 | 303.1 | 10166.8 | 0.97 s | 1.29 s | 100 % · 100 % · 100 % · 100 % |
| 16 | 10.78 | 401.4 | 13482.3 | 1.38 s | 2.01 s | 95 % · 97 % · 92 % · 92 % |
| 32 | 14.25 | 520.1 | 17819.6 | 2.06 s | 3.77 s | 88 % · 89 % · 90 % · 90 % |
| 64 | 18.60 | 687.7 | 23268.1 | 3.15 s | 5.37 s | 89 % · 92 % · 92 % · 92 % |
| 128 | 24.40 | 912.2 | 30533.8 | 4.85 s | 9.35 s | 92 % · 94 % · 94 % · 95 % |
| 256 | 30.20 | 1123.0 | 37785.8 | 8.58 s | 13.64 s | 100 % · 99 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 2.20 | 81.0 | — |
| 8 | 8.12 | 303.1 | — |
| 16 | 10.78 | 401.4 | — |
| 32 | 14.25 | 520.1 | — |
| 64 | 18.60 | 687.7 | — |
| 128 | 24.40 | 912.2 | — |
| 256 | 29.84 | 1,109 | 1.01× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 40.2 s | 2.19 | 80.5 | 0.46 s | 2.19 answers/s |
| 8 | 41.4 s | 7.85 | 292.7 | 1.00 s | 8.04 answers/s |
| 16 | 41.4 s | 10.40 | 387.5 | 1.50 s | 10.67 answers/s |
| 32 | 41.4 s | 13.75 | 502.0 | 2.28 s | 14.04 answers/s |
| 64 | 41.4 s | 17.95 | 663.7 | 3.50 s | 18.29 answers/s |
| 128 | 42.6 s | 22.93 | 857.4 | 5.41 s | 23.67 answers/s |
| 256 | 42.6 s | 28.33 | 1053.3 | 8.80 s | 29.09 answers/s |

**Prompt mix at concurrency 32:** uniform 15.72 answers/s, 570.9 tok/s, p50 2.01 s · mixed 3.15 answers/s, 1,128.8 tok/s, p50 16.23 s.

## Above 256 clients

<!-- protocol v1 · DEVIATION levels 384,512,768 and 1024 · otherwise as above -->

**Thinking on, 384–768**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 384 | 25.18 | 4935.4 | 37486.7 | 15.99 s | 32.40 s | 100 % · 100 % · 100 % · 99 % |
| 512 | 26.10 | 5150.1 | 38897.4 | 22.26 s | 42.73 s | 87 % · 100 % · 100 % · 99 % |
| 768 | 33.48 | 6591.8 | 49874.9 | 30.91 s | 58.91 s | 86 % · 88 % · 89 % · 86 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 384 | 24.02 | 4,707 | 1.05× |
| 512 | 23.00 | 4,539 | 1.13× |
| 768 | 24.85 | 4,892 | 1.35× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 384 | 58.5 s | 17.21 | 3372.9 | 18.00 s | 21.34 answers/s |
| 512 | 63.8 s | 16.37 | 3230.4 | 24.28 s | 21.09 answers/s |
| 768 | 76.4 s | 17.53 | 3451.5 | 33.47 s | 22.95 answers/s |

**Thinking on, 1024**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1024 | 40.30 | 8145.0 | 60252.9 | 34.75 s | 65.66 s | 93 % · 94 % · 93 % · 92 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1024 | 29.47 | 5,956 | 1.37× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1024 | 79.0 s | 20.40 | 4122.5 | 37.95 s | 26.98 answers/s |

**Thinking off, 384–768**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 384 | 31.48 | 1164.6 | 39375.2 | 12.66 s | 20.78 s | 100 % · 100 % · 100 % · 100 % |
| 512 | 33.62 | 1230.2 | 42050.9 | 16.53 s | 27.51 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 35.05 | 1291.3 | 43842.0 | 24.41 s | 42.27 s | 100 % · 100 % · 100 % · 99 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 384 | 30.33 | 1,122 | 1.04× |
| 512 | 30.97 | 1,133 | 1.09× |
| 768 | 31.46 | 1,159 | 1.11× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 384 | 43.7 s | 28.80 | 1065.7 | 12.70 s | 30.23 answers/s |
| 512 | 45.9 s | 29.33 | 1073.1 | 16.55 s | 30.93 answers/s |
| 768 | 46.9 s | 29.87 | 1100.5 | 24.66 s | 31.14 answers/s |

## Reading

**With thinking the curve climbs to the last level measured.** Over the real run time: 3,869
tok/s at 256 clients, 4,892 at 768 and **5,956 at 1,024**, the cards at 92–94 %. Concurrency ÷
mean latency gives 5,453 at 1,024, and the wall-clock time 4,123, tail included; the median-based
figure is the one every other page uses. From 64 to 128 clients the rate doubles at unchanged
latency, the same step MiMo, Beam and Hy3 showed under this vLLM.

**The stock engine beats the August patchset at every common level.** Read the same way, the
SGLang stack with DSpark and data-parallel attention reached 2,762 tok/s at 256 with its shipped
settings and 4,438 at 1,024, its best (`--max-running-requests 1024`). vLLM 0.33 without a draft
model gives 3,869 and 5,956: 40 % and 34 % more.

**Without thinking the answers are 37 tokens and prefill sets the ceiling:** 29.8 answers/s at
256, 31.5 at 768, about 39 k tok/s counting the prompts. The
[two-card machine](../../../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-flash-0731/) with the
SGLang patchset delivers 32.1–33.4 answers/s on half the cards.
