# Scenario: long context — Hy3, TP=4

**Setup:** [vLLM 0.33.0 TP=4, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 21:03–21:07

| Target | Prefill (TTFT) | Prefill throughput | Needles |
|---|---|---|---|
| 64,000 | 23.5 s | 2,726 tok/s | **3 of 3** |
| 128,000 | 54.1 s | 2,368 tok/s | **3 of 3** |
| 250,000 | 141.8 s | 1,763 tok/s | **3 of 3** |

Every needle found, but **the slowest prefill of the vLLM runs on these cards**: 250k tokens
take 2 min 22 s before the first answer token, against 54 s for Beam-1.0 and 19 s for the
DeepSeek EXL3 pack. Decode behind a 64k prompt drops from 85 to 74.9 tok/s.

The KV pool holds 307,936 tokens, 1.17 requests of full length: after 280 GiB of weights
about 12 GB per card are left for cache. Two long documents at once do not fit.
