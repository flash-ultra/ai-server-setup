# Scenario: reasoning cost — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4](../README.md) · `MiMo-V2.6-Flash-RL` · [the four-card machine](../../../README.md) · measured 2026-11-06, 17:12–17:16

## Method

Protocol [`v1`](../../../../benchmark/README.md), `--scenario reasoning --thinking-key enable_thinking`,
key verified against `reasoning_tokens` before the run.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|---|
| 8 | default | 6.92 | 473.5 | 68 | 22 % | 319 | 1.15 s |
| 8 | `reasoning_effort=low` | 6.97 | 473.8 | 68 | 21 % | 320 | 1.14 s |
| 8 | thinking off | **9.57** | 455.5 | 48 | 0 % | 291 | **0.82 s** |
| 32 | default | 14.38 | 962.2 | 67 | 21 % | 316 | 2.24 s |
| 32 | `reasoning_effort=low` | 14.15 | 961.6 | 68 | 22 % | 315 | 2.24 s |
| 32 | thinking off | **19.62** | 925.7 | 47 | 0 % | 290 | **1.61 s** |

**Thinking costs 1.4× in answers per second, and `low` changes nothing** — the same 68
tokens, the same 21 % reasoning, within noise of the default. The two-card series found
exactly this (4.67 / 4.80 / 6.83 answers/s at C=8). On this prompt the model already thinks
at the minimum; there is nothing for `low` to cut.
