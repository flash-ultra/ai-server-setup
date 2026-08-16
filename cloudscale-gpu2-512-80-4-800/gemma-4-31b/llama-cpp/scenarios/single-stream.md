# Scenario: single stream — llama.cpp

One request at a time, nothing else on the machine.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-31B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1` — concurrency 1, prompt verbatim, `max_tokens` 512, 40 s window, 3 discarded
warmups, counts from `usage`. MTP active, thinking at the checkpoint default (on). The
other three cards were idle.

## Measurement

| Metric | Value |
|---|---|
| Output | 54.8 tok/s |
| Total (incl. prompt) | 208.0 tok/s |
| Requests | 0.12 req/s |
| Latency p50 | 8.10 s |
| Tokens per answer | 438 |
| GPU utilisation | 94 % |

## Reading

**Slower than the sparse sibling by a factor of 3.5** — 54.8 against 189.8 output tokens
per second for [Gemma-4-26B-A4B](../../../gemma-4-26b-a4b/llama-cpp/scenarios/single-stream.md),
at a comparable total parameter count. This is the cost of activating every parameter for
every token.

**94 % utilisation is the highest this model reaches.** It falls steadily as concurrency
rises, down to 33 % at 32 — see [concurrent load](concurrent-load.md).

**438 tokens per answer against a 512 budget**, with thinking on. Most of that is trace;
[reasoning cost](reasoning-cost.md) separates the two.

## Not measured

- Time to first token — the protocol's single-stream scenario reports end-to-end latency
- The same figure without MTP. The [control run](../README.md) covers the sparse sibling
