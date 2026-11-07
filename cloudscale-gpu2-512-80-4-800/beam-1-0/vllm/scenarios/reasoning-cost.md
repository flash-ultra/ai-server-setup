# Scenario: reasoning cost — Beam-1.0, TP=4

**Setup:** [vLLM 0.33.0 TP=4, NVFP4](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 19:43–19:49

<!-- protocol v1 · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Latency p50 |
|---|---|---|---|---|---|---|
| 8 | default (max) | 1.75 | 431.6 | 247 | 83 % | 4.44 s |
| 8 | `reasoning_effort=low` | 1.82 | 427.0 | 234 | 82 % | 4.42 s |
| 8 | `enable_thinking: false` (not a switch here) | 1.93 | 432.4 | 225 | 81 % | 4.17 s |
| 32 | default (max) | 3.73 | 880.3 | 236 | 82 % | 9.10 s |
| 32 | `reasoning_effort=low` | 3.75 | 880.2 | 235 | 82 % | 8.99 s |
| 32 | `enable_thinking: false` (not a switch here) | 3.85 | 875.6 | 227 | 81 % | 9.14 s |

All three variants within 10 % of each other: on this prompt the budget hint changes almost
nothing.
