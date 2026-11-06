# Scenario: single stream — Strata DeepSeek engine

**Setup:** [Strata 0.2.11, `strata-dsv41`, `DS4_SPLIT=10,10,10,10`](../README.md) · `DeepSeek-V4.1-Flash-1017` GSQ-RCO 2.25 bpw · [the four-card machine](../../../README.md) · measured 2026-11-06, 20:46–20:48

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations. Strata reports no
`reasoning_tokens`, so the reasoning share reads 0 % — not reported, not absent. The
1,500-token decode rows generated 213 tokens: Strata honours neither `min_tokens` nor `ignore_eos`.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **111.8 tok/s** | 104.7 tok/s |
| Requests | 0.53 req/s | **1.48 req/s** |
| Latency p50 | 1.95 s | **0.69 s** |
| Tokens per answer | 213 | 71 |
| GPU utilisation | 26 · 22 · 22 · 28 % | 26 · 22 · 23 · 27 % |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 213 / 213 | 0.03 / 0.03 s | **110.2 / 110.0 tok/s** |
| thinking off, run 1 / 2 | 71 / 71 | 0.02 / 0.02 s | **105.4 / 105.3 tok/s** |
| thinking on, "1,500 tokens", run 1 / 2 | 213 / 213 | 0.02 / 0.02 s | **110.0 / 109.9 tok/s** |
| thinking on, behind a 64k prompt | 160 | 16.45 s | **106.5 tok/s** |

**110 tok/s whatever the context, at a quarter of each card.** With the automatic split
the same stream ran at 109.8 tok/s ([setup](../README.md#the-automatic-layer-split-and-how-to-override-it)):
decode passes the layers one after another, so where they sit does not matter for one
client. The EXL3 pack on two of these cards decodes 114–128 and runs the single stream at 136.5.
