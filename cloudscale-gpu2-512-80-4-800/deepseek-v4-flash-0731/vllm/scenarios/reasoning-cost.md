# Scenario: reasoning cost — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-08, 00:05–00:10

Protocol [`v1`](../../../../benchmark/README.md), thinking key `thinking`. The server sets
`thinking: true` as its default, so "default" is the thinking arm.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 2.08 | 449.2 | 217 | 81 % | 247 | 3.58 s | 100 % · 100 % · 100 % · 100 % |
| 8 | reasoning_effort=low | 1.40 | 406.8 | 291 | 85 % | 277 | 5.92 s | 95 % · 95 % · 96 % · 96 % |
| 8 | thinking off (thinking) | 8.05 | 302.8 | 38 | 0 % | 229 | 0.97 s | 100 % · 100 % · 99 % · 100 % |
| 32 | default | 5.45 | 1030.0 | 189 | 79 % | 239 | 5.39 s | 100 % · 100 % · 100 % · 100 % |
| 32 | reasoning_effort=low | 3.38 | 1036.0 | 307 | 86 % | 266 | 10.61 s | 100 % · 100 % · 100 % · 100 % |
| 32 | thinking off (thinking) | 15.53 | 573.8 | 37 | 0 % | 225 | 2.03 s | 99 % · 100 % · 99 % · 100 % |

**Thinking off answers 2.9 to 3.9 times as often** with a visible answer of about the same
length: 225–229 characters against 239–247, in 37–38 tokens against 189–217. Four fifths of a
thinking answer are reasoning.

**`reasoning_effort: low` makes the answers longer, not shorter:** 291–307 tokens against the
default's 189–217, and a third fewer answers per second. On this release it is no way to save
tokens.
