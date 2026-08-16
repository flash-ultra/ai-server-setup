# Scenario: single stream — llama.cpp

One request at a time, nothing else on the machine.

**Setup:** [llama.cpp single-card](../README.md) · Muse-Glimmer-30B BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1` — concurrency 1, prompt verbatim, `max_tokens` 512, 40 s window, 3 discarded
warmups, counts from `usage`. No speculative decoding. The other three cards were idle.

## Measurement

| Metric | Value |
|---|---|
| Output | 30.9 tok/s |
| Total (incl. prompt) | 126.0 tok/s |
| Requests | 0.07 req/s |
| Latency p50 | 14.78 s |
| Tokens per answer | 413 |
| GPU utilisation | **97 %** |

## Reading

**The slowest single-stream figure of the three models measured on this machine** — 30.9
output tokens per second against 54.8 for the dense
[Gemma-4-31B](../../../gemma-4-31b/llama-cpp/scenarios/single-stream.md) and 189.8 for the
sparse [Gemma-4-26B-A4B](../../../gemma-4-26b-a4b/llama-cpp/scenarios/single-stream.md).
Part of the gap is the missing speculation, which is worth 37–49 % at low concurrency on
the Gemma checkpoints; the rest is a dense 30 B forward pass.

**97 % utilisation, and it stays there.** Unlike both Gemma runs, this model holds
92–99 % across the whole concurrency sweep — the observation that made it the control for
llama.cpp's idle time on the other two.

## Not measured

- Time to first token
- The same figure with a draft model, which exists upstream but not in this GGUF package
