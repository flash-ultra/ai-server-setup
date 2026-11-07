# Scenario: long context — Beam-1.0, TP=4

**Setup:** [vLLM 0.33.0 TP=4, NVFP4](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 19:49–19:51

| Target | Prefill (TTFT) | Prefill throughput | GPU | Needles |
|---|---|---|---|---|
| 64,000 | 12.4 s | 5,163 tok/s | 100 % | **3 of 3** |
| 128,000 | 25.8 s | 4,969 tok/s | 98–100 % | **3 of 3** |
| 250,000 | 54.2 s | 4,616 tok/s | 96 % | **3 of 3** |

Every needle found; prefill 11 % slower at 250k than at 64k. Decode behind 64k: 96.0 tok/s.
