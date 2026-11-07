# Scenario: single stream — Nemotron-3-Super, DP=4

**Setup:** [vLLM 0.33.0, four copies](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 17:56–17:57 and 18:17

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations. One request reaches one copy
on one card.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **83.1 tok/s** | 76.4 tok/s |
| Requests | 0.50 req/s | 1.07 req/s |
| Latency p50 | 2.01 s | 0.96 s |
| Tokens per answer | 166 (63 % reasoning) | 71 |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 137 / 170 | 0.16 / 0.14 s | **87.0 / 87.2 tok/s** |
| thinking off, run 1 / 2 | 73 / 71 | 0.18 / 0.15 s | **87.0 / 86.6 tok/s** |
| thinking on, 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.35 / 0.34 s | **86.5 / 87.1 tok/s** |
| thinking on, behind a 64k prompt | 163 | 5.70 s | **86.9 tok/s** |

**87 tok/s, the same to one decimal place in every row.** Twelve billion active
parameters on one card, without the MTP head; context does not slow it, because the Mamba
layers carry a fixed-size state instead of a growing cache.
