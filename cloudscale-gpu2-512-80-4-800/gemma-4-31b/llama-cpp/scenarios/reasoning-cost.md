# Scenario: reasoning cost — llama.cpp

What thinking costs per answer, and why turning it off buys nothing here.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-31B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1`, concurrency 8 and 32. **Deviation:** `--thinking-key enable_thinking` —
the protocol default `thinking` is not read by this template and does nothing. Verified
before the run against `reasoning_content` length.

## Measurements

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|
| 8 | default | 0.20 | 85.8 | 429 | 181 | 72.94 s | 72 % |
| 8 | `reasoning_effort=low` | 0.20 | 84.3 | 422 | 224 | 93.42 s | 54 % |
| 8 | thinking off | 0.20 | 7.2 | **36** | 216 | 63.10 s | 15 % |
| 32 | default | 0.80 | 316.5 | 396 | 196 | 129.59 s | 30 % |
| 32 | `reasoning_effort=low` | 0.80 | 323.8 | 405 | 175 | 119.70 s | 36 % |
| 32 | thinking off | 0.80 | 28.0 | **35** | 214 | 110.37 s | 13 % |

The reasoning-share column reads 0 % throughout and is omitted — llama.cpp does not send
`reasoning_tokens`. Tokens per answer carries the same information: 429 tokens for a
181-character answer is a trace.

## Reading

**Thinking costs 12× the tokens and delivers the same answer length.** 429 tokens down
to 36 at concurrency 8, while characters per answer stay at 181 against 216. Almost the
entire generation is trace.

**And removing it changes the answers per second not at all.** 0.20 before, 0.20 after;
0.80 before, 0.80 after. The saving is real in tokens and invisible in throughput,
because with a ~1000-token prompt and a 36-token answer the request is dominated by
prefill. Utilisation drops to 13–15 %: the card spends the window waiting, not
generating.

> **This is the opposite of what the same change does on the MoE sibling.**
> [Gemma-4-26B-A4B](../../../gemma-4-26b-a4b/llama-cpp/scenarios/reasoning-cost.md) gains
> 2.6× answers per second from the identical switch, because its decode is fast enough
> that decode was the bottleneck. A thinking-off saving only materialises where decode
> was the limit — the same option is worth a factor of 2.6 on one model and nothing on
> another, on the same card and engine.

**`reasoning_effort` is inert on this checkpoint.** 422 against 429 tokens. Only the
chat-template switch works.

## Not measured

- Answer quality without thinking
- Whether a shorter prompt would move this model into the regime where thinking-off pays
  — the protocol prompt is fixed at ~1000 tokens, and that is what makes prefill dominant
  here
