# Scenario: concurrent load — Strata DeepSeek engine, 8 slots

**Setup:** [Strata 0.2.11, `strata-dsv41`, `DS4_SPLIT=10,10,10,10`, `--parallel 8`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-06, 20:50–21:03

## Method

Protocol [`v1`](../../../../benchmark/README.md) with the same deviation as the
[Qwen Strata series](../../../qwen3-8-flash-next/strata/scenarios/concurrent-load.md):
**levels 1, 4, 8, 16**, because the engine serves at most eight requests at once.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · DEVIATION: levels 1,4,8,16 -->

| Concurrent | thinking on: answers/s | output tok/s | p50 | thinking off: answers/s | output tok/s | p50 | GPU (on) |
|---|---|---|---|---|---|---|---|
| 1 | 0.53 | **111.8** | 1.94 s | 1.48 | 104.7 | 0.68 s | 26 · 22 · 22 · 28 % |
| 4 | 1.50 | 156.0 | 2.71 s | 2.20 | 156.2 | 1.86 s | 28 · 21 · 20 · 30 % |
| 8 | 1.40 | 159.6 | 6.03 s | 2.40 | 163.2 | 3.51 s | 29 · 20 · 19 · 30 % |
| 16 | 1.60 | 182.4 | 11.87 s | 2.60 | 176.8 | 6.80 s | 30 · 20 · 21 · 30 % |
| 32, uniform | 2.00 | 228.0 | 23.69 s | 3.00 | 204.0 | 13.59 s | |
| 32, mixed | 0.80 | 384.9 | 109.32 s | 1.05 | 446.8 | 75.32 s | |

**Eight slots buy 1.4× over one client.** The cards never pass 30 %, so this is the engine's
limit: each slot advances its own ring through the pipeline, and the rings are not batched
into one matrix product the way vLLM or Strata's Qwen engine batch them. For comparison at
C=8 on the same cards: Strata Qwen IQ3_S 645.5, MiMo under vLLM 465.2, this 159.6.
