# Scenario: single stream — llama.cpp

One request at a time, nothing else on the machine. The interactive single-user case.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-26B-A4B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1` — concurrency 1, prompt verbatim from `bench.py`, `max_tokens` 512, 40 s
window, 3 discarded warmups, counts from `usage`. MTP speculative decoding active. The
other three cards were idle.

## Measurement

| Metric | Value |
|---|---|
| Output | **189.8 tok/s** |
| Total (incl. prompt) | 649.5 tok/s |
| Requests | 0.38 req/s |
| Latency p50 | **2.80 s** |
| Tokens per answer | 506 |
| GPU utilisation | 83 % |

## Reading

**The fastest single-stream figure measured on this machine so far** — 189.8 output
tokens per second against 60.0 for the dense
[Gemma-4-31B](../../../gemma-4-31b/llama-cpp/scenarios/single-stream.md), 28.6 for
[Muse Glimmer](../../../muse-glimmer-30b/llama-cpp/scenarios/single-stream.md), and
131.2 for DeepSeek-V4-Flash on all four cards under SGLang. A sparse model on one card
beats a much larger sparse model on four, for a single user.

**506 tokens per answer against a 512-token budget.** The answer is at the cap, which
means the generation was truncated rather than finished — with thinking on, the trace
consumes the budget. What this row measures is generation speed, not a completed answer;
[reasoning cost](reasoning-cost.md) shows what the same request looks like with the trace
switched off.

**Utilisation is 83 %, and that is the high point.** It falls as concurrency rises,
which is discussed in [concurrent load](concurrent-load.md) — the short version is that
a model with 4 B active parameters does too little work per forward pass to keep the card
saturated between steps.

## Not measured

- Time to first token. The protocol's single-stream scenario reports end-to-end latency;
  TTFT would need the streaming path
- Generation speed with the trace off, in isolation. It appears only inside the reasoning
  scenario, at concurrency 8 and 32
