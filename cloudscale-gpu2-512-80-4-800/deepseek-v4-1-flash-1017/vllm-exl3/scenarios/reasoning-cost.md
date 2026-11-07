# Scenario: reasoning cost — EXL3 on four cards

**Setup:** [pack recipe, `PROFILE=8x REPLICA=0`](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|---|
| 8 | default | 2.80 | 472.7 | 169 | 76 % | 251 | 2.85 s |
| 8 | `reasoning_effort=low` | 3.02 | 446.2 | 148 | 72 % | 256 | 2.64 s |
| 8 | thinking off | **5.25** | 292.8 | 56 | 0 % | 348 | **1.56 s** |
| 32 | default | 5.80 | 973.5 | 168 | 76 % | 252 | 5.70 s |
| 32 | `reasoning_effort=low` | 6.22 | 924.8 | 149 | 72 % | 254 | 5.33 s |
| 32 | thinking off | **10.75** | 591.1 | 55 | 0 % | 343 | **3.14 s** |

Thinking costs 1.9× in answers per second; `low` trims 12 % of the tokens. Unlike Strata's
DeepSeek engine, where `low` made the model think longer, the pack's encoder maps it as
intended (`v41-encoder-api.diff`: "reasoning_effort aliases").
