# Scenario: single stream — Beam-1.0, TP=4

**Setup:** [vLLM 0.33.0 TP=4, NVFP4](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 19:34 and 19:49

Protocol [`v1`](../../../../benchmark/README.md), default arm only (no off switch).

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking on (default, effort max) |
|---|---|
| Output | **98.2 tok/s** |
| Requests | 0.40 req/s |
| Latency p50 | 2.51 s |
| Tokens per answer | 246 (83 % reasoning) |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| default, run 1 / 2 | 178 / 170 | 0.09 / 0.08 s | **98.7 / 98.9 tok/s** |
| `enable_thinking: false` (no effect), run 1 / 2 | 355 / 172 | 0.07 / 0.07 s | **98.0 / 98.9 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.46 / 0.08 s | **97.1 / 96.8 tok/s** |
| behind a 64k prompt | 246 | 12.21 s | **96.0 tok/s** |

**98 tok/s, flat** — 23 B active parameters at 4 bits, without a draft head.
