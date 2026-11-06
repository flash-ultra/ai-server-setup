# Scenario: reasoning cost — Strata IQ3_S, four cards

Cost of thinking per answer at concurrency 8 and 32 (the latter above the slot limit).

**Setup:** [Strata 0.2.11, IQ3_S, four cards, 8 slots](../README.md) ·
[the four-card machine](../../../README.md) · measured 2026-11-06, 12:18–12:23

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md),
`bench.py --scenario reasoning --thinking-key enable_thinking`, key verified (50 → 4
completion tokens). The reasoning column reads 0 % because Strata reports no
`reasoning_tokens`; the tokens-per-answer column carries the information.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|
| 8 | default | 3.20 | 638.5 | 200 | 268 | 2.57 s | 64 · 63 · 65 · 75 % |
| 8 | `reasoning_effort=low` | 4.28 | 587.5 | 137 | 300 | 1.88 s | 64 · 68 · 63 · 80 % |
| 8 | thinking off | **7.97** | 406.1 | 51 | 324 | **0.98 s** | 49 · 39 · 37 · 50 % |
| 32 | default | 3.62 | 769.8 | 212 | 264 | 8.26 s | 68 · 60 · 62 · 79 % |
| 32 | `reasoning_effort=low` | 4.95 | 679.6 | 137 | 307 | 5.82 s | 61 · 61 · 62 · 72 % |
| 32 | thinking off | **8.72** | 445.9 | 51 | 327 | **2.91 s** | 53 · 53 · 56 · 67 % |

**Thinking costs 2.5× in answers per second at C=8 and 2.6× in latency**, the same shape
as [under vLLM](../../vllm/scenarios/reasoning-cost.md) (2.9×), and `low` buys back a third
(137 tokens). At C=32 the thinking-off arm still answers 8.7 per second behind eight slots,
because each answer holds a slot for a third of a second.

## The Q8_0 pack, same engine

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|
| 8 | default | 2.70 | 534.7 | 198 | 260 | 2.95 s |
| 8 | `reasoning_effort=low` | 3.48 | 509.6 | 147 | 314 | 2.31 s |
| 8 | thinking off | **6.78** | 340.3 | 50 | 320 | **1.16 s** |
| 32 | default | 3.35 | 665.1 | 199 | 264 | 8.87 s |
| 32 | `reasoning_effort=low` | 4.12 | 591.6 | 143 | 303 | 7.37 s |
| 32 | thinking off | **7.38** | 369.3 | 50 | 319 | **3.53 s** |

Thinking costs 2.5× at C=8, as with the 3-bit pack.
