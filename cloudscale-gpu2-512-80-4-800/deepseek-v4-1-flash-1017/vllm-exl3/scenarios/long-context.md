# Scenario: long context — EXL3 on four cards

**Setup:** [pack recipe, `PROFILE=8x REPLICA=0`, 1 M context](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 11:45–11:48

## Method

Protocol [`v1`](../../../../benchmark/README.md), targets 64k, 128k, 250k and **960k** (the
depth the two-card series measured), needles at 10 / 50 / 90 %, thinking on, idle engine.

## Result

| Target | Prefill (TTFT) | Prefill throughput | GPU | Needles |
|---|---|---|---|---|
| 64,000 | 6.1 s | 10,470 tok/s | 76–82 % | **3 of 3** |
| 128,000 | 9.5 s | **13,408 tok/s** | 80–94 % | **3 of 3** |
| 250,000 | 18.8 s | **13,264 tok/s** | 92–98 % | **3 of 3** |
| 960,000 | 87.6 s | 10,959 tok/s | 95–97 % | **3 of 3** |

**A million-token prompt in 88 seconds, every needle found.** The two-card series read
180k at 11,386 tok/s and 960k at 9,123; four cards add 15–20 %. Only Strata's Qwen engine
reads faster on this machine (21,873 tok/s at 250k), and its window ends at 262k.
