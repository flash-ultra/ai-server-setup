# Scenario: concurrent load — Beam-1.0, TP=4

**Setup:** [vLLM 0.33.0 TP=4, NVFP4](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 19:35–19:43

Protocol [`v1`](../../../../benchmark/README.md), full ladder, default arm only.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| 1 | 0.45 | 102.8 | 668.4 | 2.29 s | 3.26 s |
| 8 | 1.82 | 427.7 | 2721.8 | 4.31 s | 6.16 s |
| 16 | 2.73 | 630.7 | 4056.1 | 5.92 s | 9.14 s |
| 32 | 3.77 | 857.1 | 5602.3 | 8.45 s | 15.15 s |
| 64 | 5.00 | 1184.7 | 7469.6 | 13.70 s | 22.98 s |
| 128 | 10.38 | 2402.9 | 15444.3 | 13.82 s | 21.49 s |
| 256 | **14.93** | **3472.2** | 22232.9 | 20.03 s | 31.88 s |

**Prompt mix at concurrency 32:** uniform 3.80 answers/s, 878.0 tok/s, p50 9.14 s · mixed 1.77 answers/s, 868.2 tok/s, p50 22.14 s.

**From 64 to 128 clients the answer rate doubles at unchanged latency**, the same step MiMo
showed on these cards under the same vLLM; from 128 to 256 it gains another 44 %. Cards at
99–100 % from C=1 on.
