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

## Two replicas: `--replicas 2`, one engine on cards 0–1 and one on 2–3

Strata's server can cut the card list into equal groups and run one engine per group,
spreading requests over them. The model fits two cards (`DS4_SPLIT=20,20`, 80–85 GB per
card, every expert in VRAM). Same protocol, levels 1 to 32, thinking on, measured 21:24–21:29:

<!-- protocol v1 · DEVIATION levels 1,4,8,16,32 · --replicas 2 · DS4_SPLIT=20,20 · --parallel 8 each -->

| Concurrent | Answers/s | Output tok/s | vs. one engine | Latency p50 | GPU |
|---|---|---|---|---|---|
| 1 | 0.93 | 109.2 | 0.98× | 1.10 s | 49 · 50 · 0 · 0 % |
| 4 | 2.35 | **278.1** | 1.78× | 1.70 s | 48 · 51 · 44 · 51 % |
| 8 | 2.20 | **319.0** | 2.00× | 3.84 s | 44–49 % |
| 16 | 2.42 | **338.6** | 1.86× | 7.93 s | 47–49 % |
| 32, uniform | 2.80 | **389.2** | 1.71× | 15.46 s | 47–50 % |
| 32, mixed | 0.82 | 392.3 | 1.02× | 57.62 s | |

**Two engines double the throughput and halve nothing for one client.** Each card now does
half of an engine's layers instead of a quarter, so it works half the time instead of a
quarter. Four replicas would need the model on one card each; at 155 GB of experts it does
not fit. For more than one user, `--replicas 2` is the configuration to serve.

**With one engine, eight slots buy 1.4× over one client.** The cards never pass 30 %, so this is the engine's
limit: each slot advances its own ring through the pipeline, and the rings are not batched
into one matrix product the way vLLM or Strata's Qwen engine batch them. For comparison at
C=8 on the same cards: Strata Qwen IQ3_S 645.5, MiMo under vLLM 465.2, this 159.6.
