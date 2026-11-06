# Scenario: reasoning cost — Strata DeepSeek engine

**Setup:** [Strata 0.2.11, `strata-dsv41`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-06, 21:03–21:09

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|
| 8 | default | 1.40 | 159.6 | 114 | 229 | 6.05 s |
| 8 | `reasoning_effort=low` | 1.00 | 170.0 | **170** | 212 | 9.43 s |
| 8 | thinking off | **2.40** | 163.2 | 68 | 417 | **3.52 s** |
| 32 | default | 2.00 | 228.0 | 114 | 229 | 23.72 s |
| 32 | `reasoning_effort=low` | 1.60 | 272.0 | 170 | 212 | 37.35 s |
| 32 | thinking off | **3.00** | 204.0 | 68 | 417 | **13.56 s** |

**`low` makes DeepSeek think longer, not shorter** — 170 tokens per answer against 114 at the
default. DeepSeek-V4.1's chat template takes a numeric effort from 1 to 100 (default 75) or the
named levels; the engine maps `low` to something above its default on this prompt. Thinking off
writes the longest visible answer (417 characters against 229) in the fewest tokens.
