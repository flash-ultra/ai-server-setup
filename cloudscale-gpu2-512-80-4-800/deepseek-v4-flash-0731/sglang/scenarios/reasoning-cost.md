# Scenario: reasoning cost — SGLang

What thinking costs per answer, and which of the available switches actually changes
it. This checkpoint spends 95–96 % of its generated tokens on reasoning, so this is
the dominant cost factor in production.

**Setup:** [SGLang + SM120 patchset](../README.md) · DeepSeek-V4-Flash-0731 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-15

## Method

All variants are set per request — no server restart, so the comparison runs against
one identical process:

```json
{"chat_template_kwargs": {"thinking": false}}     // thinking off
{"reasoning_effort": "low" | "medium" | "high"}   // effort level
```

Same prompt as [concurrent-load.md](concurrent-load.md) (~1000 tokens),
`max_tokens` 512, 40 s per measurement, token counts from the `usage` fields including
`completion_tokens_details.reasoning_tokens`. Answer length is measured in characters
of the visible `content` field, because token counts say nothing about how much answer
the user actually receives.

## Single request

One sample per variant, different prompt (a short factual question), to check that the
switches take effect at all:

| Variant | Total tokens | Reasoning | Share | Answer | Time |
|---|---|---|---|---|---|
| default | 740 | 585 | 79 % | 518 chars | 6.21 s |
| **thinking off** | **146** | 0 | 0 % | 505 chars | **1.17 s** |
| `reasoning_effort=low` | 505 | 322 | 64 % | 653 chars | 4.44 s |
| `reasoning_effort=medium` | 576 | 402 | 70 % | 643 chars | 5.23 s |
| `reasoning_effort=high` | 627 | 417 | 67 % | 769 chars | 5.14 s |

## Under load

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 1.23 | 604.9 | 494 | 96 % | 81 | 6.83 s | 89 % |
| 8 | `reasoning_effort=low` | 1.35 | 653.4 | 484 | 96 % | 80 | 6.44 s | 93 % |
| 8 | **thinking off** | **6.08** | 335.3 | **55** | 0 % | **220** | **1.28 s** | 85 % |
| 32 | default | 3.20 | 1569.4 | 490 | 95 % | 107 | 11.47 s | 91 % |
| 32 | `reasoning_effort=low` | 3.23 | 1530.6 | 475 | 95 % | 108 | 11.54 s | 94 % |
| 32 | **thinking off** | **11.28** | 629.0 | **56** | 0 % | **223** | **2.70 s** | 85 % |

## Reading

**Tokens per second is the wrong metric for cost.** At concurrency 32 the default
configuration produces 1569 output tok/s against 629 with thinking off — it looks
2.5× better. It delivers 3.20 answers per second against 11.28. The token figure is
counting reasoning that never reaches the user; per answer, thinking costs
**490 tokens against 56, a factor of 8.75**.

**Turning thinking off makes answers longer, not shorter.** 223 characters against
107. With `max_tokens 512` and a 95 % reasoning share, roughly 25 tokens remain for
the visible answer, which is then truncated. The thinking consumes the answer's
budget. Anyone running this checkpoint with thinking on needs a substantially higher
`max_tokens` than the answer length alone suggests.

**`reasoning_effort` does effectively nothing under load.** `low` against default:
475 versus 490 tokens per answer, a 3 % difference, and answers per second are
identical within noise. The single-request table shows a wider spread (505 to 627
tokens), but that ordering does not survive contact with concurrency. The switch that
matters is binary — thinking on or off — not the graduation between levels.

**GPU utilisation barely moves.** 85 % with thinking off against 91–94 % with it on.
The cards stay busy either way; what changes is what they are busy with.

## Consequence for operation

The stack is currently configured with thinking enabled by default
(`--default-chat-template-kwargs '{"thinking": true}'` plus
`SGLANG_DSV4_REASONING_EFFORT`). That is the right default for reasoning-heavy work,
and it is what the published throughput figures were measured with.

For workloads that do not need deliberation — classification, extraction,
reformulation, routing — clients should send `chat_template_kwargs: {"thinking": false}`
per request. On this measurement that is 3.5× the answers per second at a quarter of
the latency, without changing the server configuration.

## Not measured

- Answer quality with thinking off. Only length and throughput were measured; whether
  the shorter answers are as good is a separate question and needs a task-specific
  evaluation, not a load test.
- Whether a raised `max_tokens` recovers full-length answers with thinking on, and
  what that costs in latency
- The same comparison under the [mixed prompt traffic](concurrent-load.md#prompt-mix),
  where reasoning share may differ by request shape
