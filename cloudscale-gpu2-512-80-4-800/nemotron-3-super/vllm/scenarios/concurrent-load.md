# Scenario: concurrent load — Nemotron-3-Super, DP=4

**Setup:** [vLLM 0.33.0, four copies](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 17:57–18:12

## Method

Protocol [`v1`](../../../../benchmark/README.md), full ladder, both arms, no deviations.
The GPU column reads near 100 % throughout ([why](../README.md#pinned-values)).

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | on: answers/s | output tok/s | p50 | off: answers/s | output tok/s | p50 |
|---|---|---|---|---|---|---|
| 1 | 0.53 | 82.6 | 1.92 s | 1.10 | 75.7 | 0.94 s |
| 8 | 2.25 | 391.3 | 3.40 s | 4.35 | 302.4 | 1.91 s |
| 16 | 3.45 | 609.8 | 4.41 s | 5.92 | 415.9 | 2.80 s |
| 32 | 5.08 | 869.5 | 6.32 s | 8.12 | 561.9 | 4.10 s |
| 64 | 6.72 | 1125.6 | 9.82 s | 11.88 | 813.0 | 5.64 s |
| 128 | 10.78 | 1848.5 | 12.11 s | 15.38 | 1056.6 | 8.97 s |
| 256 | **15.00** | **2591.5** | 18.37 s | **19.35** | 1358.1 | 13.79 s |
| 32, mixed | 3.27 | 1513.0 | 12.01 s | 3.35 | 1531.1 | 12.35 s |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | on: answers/s | output tok/s | v1 over by | off: answers/s | output tok/s | v1 over by |
|---|---|---|---|---|---|---|
| 1 | 0.52 | 81.2 | 1.02× | 1.06 | 73.2 | 1.03× |
| 8 | 2.25 | 391.3 | — | 4.19 | 291.2 | 1.04× |
| 16 | 3.45 | 609.8 | — | 5.71 | 401.4 | 1.04× |
| 32 | 5.06 | 866.6 | — | 7.80 | 540.1 | 1.04× |
| 64 | 6.52 | 1,092 | 1.03× | 11.35 | 776.6 | 1.05× |
| 128 | 10.57 | 1,812 | 1.02× | 14.27 | 980.3 | 1.08× |
| 256 | 13.94 | 2,408 | 1.08× | 18.56 | 1,303 | 1.04× |

**Still climbing at 256**, with 10.7 M tokens of cache per copy unused. The mixed run is
the best of the series at C=32 (1,513 output tok/s): the long-analysis prompt that holds
every other model's batch back costs this one almost nothing in prefill.
