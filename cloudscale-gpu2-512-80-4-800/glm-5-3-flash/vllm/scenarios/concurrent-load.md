# Scenario: concurrent load — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4 EP, NVFP4](../README.md) · `GLM-5.3-Flash` · [the four-card machine](../../../README.md) · measured 2026-11-06, 18:19–18:29

## Method

Protocol [`v1`](../../../../benchmark/README.md), levels 1 to 256, **default arm only**
(thinking cannot be switched off), plus the mixed run at 32.

## Result, thinking on (default, effort max)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.28 | 101.7 | 438.0 | 3.87 s | 5.11 s | 99 % × 4 |
| 8 | 1.12 | 394.7 | 1770.5 | 7.38 s | 10.98 s | 96–97 % |
| 16 | 1.45 | 540.7 | 2314.1 | 11.28 s | 17.05 s | 100 % × 4 |
| 32 | 2.08 | 723.5 | 3261.3 | 16.26 s | 28.44 s | 100 % × 4 |
| 64 | 2.40 | 930.2 | 3865.4 | 32.52 s | 44.69 s | 96 % × 4 |
| 128 | 3.25 | 1248.6 | 5223.3 | 49.95 s | 55.84 s | 100 % × 4 |
| 256 | **6.40** | **2346.7** | 10173.9 | **86.24 s** | 94.02 s | 100 % × 4 |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 2.05 | 713.0 | 3220.2 | 17.63 s | 29.09 s |
| mixed | 1.62 | 829.2 | 2192.7 | 19.88 s | 22.67 s |

## Reading it

**Above 64 clients the median answer takes longer than the 40-second measurement window**,
so the answers counted at 128 and 256 are the ones that started in the warmup or early in
the window; the answer rates there are a lower bound, and the latencies are what a client
would see. The token rate climbs normally — 2,347 tok/s at 256, level with Qwen — but
each answer is 360–380 tokens of which five in six are thinking. At `reasoning_effort: "low"`
the same cards answer 2.8× as often at C=8 ([reasoning cost](reasoning-cost.md)).
