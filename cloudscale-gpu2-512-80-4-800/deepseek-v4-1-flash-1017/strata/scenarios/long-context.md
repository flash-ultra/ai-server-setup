# Scenario: long context — Strata DeepSeek engine

**Setup:** [Strata 0.2.11, `strata-dsv41`, `DS4_SPLIT=10,10,10,10`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-06, 20:48–20:50

## Result

<!-- protocol v1 · counted via usage fields -->

| Target | Prefill (TTFT) | Prefill throughput | GPU | Needles |
|---|---|---|---|---|
| 64,000 | 15.7 s | **4,079 tok/s** | 62 · 62 · 72 · 81 % | **3 of 3** |
| 128,000 | 29.6 s | **4,321 tok/s** | 72 · 76 · 83 · 72 % | **3 of 3** |
| 250,000 | 60.1 s | **4,159 tok/s** | 81 · 73 · 93 · 74 % | **3 of 3** |

Flat to 250k, every needle found. With the engine's automatic split the 64k prompt took
29.7 s (2,154 tok/s); the even split halves that. The EXL3 pack on two of these cards reads
180k at 11,386 tok/s and has found all three needles at 960k.
