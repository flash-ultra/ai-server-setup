# Scenario: reasoning cost — Nemotron-3-Super, DP=4

**Setup:** [vLLM 0.33.0, four copies](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 18:12–18:17

<!-- protocol v1 · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Latency p50 |
|---|---|---|---|---|---|---|
| 8 | default | 2.40 | 419.6 | 175 | 66 % | 3.17 s |
| 8 | `reasoning_effort=low` | 2.40 | 418.6 | 174 | 65 % | 3.24 s |
| 8 | thinking off | **4.38** | 303.8 | 69 | 0 % | **1.88 s** |
| 32 | default | 5.33 | 938.1 | 176 | 66 % | 5.75 s |
| 32 | `reasoning_effort=low` | 5.45 | 896.8 | 165 | 63 % | 5.96 s |
| 32 | thinking off | **8.18** | 569.4 | 70 | 0 % | **4.11 s** |

Thinking costs 1.5–1.8× in answers per second. `reasoning_effort=low` does nothing: this
model's low setting is a chat-template switch (`low_effort: true`), which the protocol's
`reasoning` scenario does not send.
