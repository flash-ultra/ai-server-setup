# Scenario: reasoning cost — vLLM TP=4

What thinking costs per answer at concurrency 8 and 32: default effort, `reasoning_effort=low`,
and thinking off.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md) · `Qwen3.8-Flash-Next-FP8` ·
[the four-card machine](../../../README.md) · measured 2026-11-06

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md),
`bench.py --scenario reasoning --thinking-key enable_thinking`. The key was verified
against `usage.completion_tokens_details.reasoning_tokens` before the run (44 → 0).
`reasoning_effort=low` is passed as the top-level request field; the template's own
levels are xhigh (default), medium and low.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|---|
| 8 | default | 2.15 | 463.0 | 215 | 79 % | 259 | 3.62 s |
| 8 | `reasoning_effort=low` | 2.95 | 426.8 | 145 | 65 % | 303 | 2.75 s |
| 8 | thinking off | **6.28** | 315.8 | 50 | 0 % | 318 | **1.25 s** |
| 32 | default | 4.35 | 876.0 | 201 | 78 % | 261 | 7.48 s |
| 32 | `reasoning_effort=low` | 5.50 | 812.6 | 148 | 64 % | 312 | 6.09 s |
| 32 | thinking off | **10.60** | 528.3 | 50 | 0 % | 317 | **3.02 s** |

**Thinking costs 2.9× in answers per second and 2.4–2.9× in latency on a summary
prompt**, for 4.3× the tokens, of which four in five are the thinking trace. `low` buys a
third of that back (145 tokens, 2.95 answers/s). The visible answer is longest with
thinking off (318 chars against 259): the model that thought writes a shorter summary.
Same shape as every reasoning model measured in this series.
