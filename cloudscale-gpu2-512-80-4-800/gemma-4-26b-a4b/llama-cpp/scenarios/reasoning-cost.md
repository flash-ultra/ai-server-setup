# Scenario: reasoning cost — llama.cpp

What thinking costs per answer, and what turning it off changes.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-26B-A4B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1`, concurrency 8 and 32, three variants per level.

**Deviation:** `--thinking-key enable_thinking`. The protocol default is `thinking`,
which this checkpoint's template does not read — sending it is accepted and does
nothing. Verified before the run: with `thinking: false` the reasoning trace stayed at
1771 characters; with `enable_thinking: false` it went to zero.

## Measurements

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|
| 8 | default | 0.60 | 305.1 | 508 | **56** | 17.98 s | 77 % |
| 8 | `reasoning_effort=low` | 0.60 | 305.2 | 509 | 32 | 18.15 s | 77 % |
| 8 | **thinking off** | **2.38** | 108.0 | **45** | **280** | **3.03 s** | 51 % |
| 32 | default | 1.60 | 818.1 | 511 | **11** | 28.84 s | 55 % |
| 32 | `reasoning_effort=low` | 1.55 | 787.2 | 508 | 34 | 31.12 s | 50 % |
| 32 | **thinking off** | **4.17** | 189.8 | **45** | **278** | **6.35 s** | 28 % |

The reasoning share column that `bench.py` prints reads 0 % on every row and is omitted:
llama.cpp does not send `reasoning_tokens` in `usage`, so the field is absent rather than
zero. The reasoning is visible in `reasoning_content` and in the tokens-per-answer
column — 511 tokens for an 11-character answer is the trace, not the answer.

## Reading

**With thinking on, the answer is the part that gets truncated.** At concurrency 32 the
model spends 511 tokens and emits **11 characters**. The `max_tokens` 512 budget is
consumed by the trace, and what reaches the user is a stub. Throughput looks excellent
while the output is unusable — which is exactly why a token-per-second number alone
cannot decide anything here.

**Turning thinking off gives 2.6× the answers per second and a longer answer.** 1.60 to
4.17 at concurrency 32, tokens per answer down 11×, and characters per answer up from 11
to 278. Both improve, because they were measuring different halves of the same problem.

**`reasoning_effort` does nothing on this checkpoint.** 509 against 508 tokens per
answer. The control that works here is the chat-template switch; the top-level parameter
is accepted and ignored. On
[Muse Glimmer](../../../muse-glimmer-30b/llama-cpp/scenarios/reasoning-cost.md) the
relationship is exactly reversed.

**The gain is not universal.** The dense
[Gemma-4-31B](../../../gemma-4-31b/llama-cpp/scenarios/reasoning-cost.md) shows the same
12× token reduction with **no** change in answers per second, because its bottleneck is
prefill rather than decode. Thinking-off is a decode-side saving; it only shows up where
decode was the limit.

## Not measured

- **Answer quality without thinking.** Characters per answer rise, which says nothing
  about whether the answers are as good. This is the same open question the DeepSeek-V4
  series carries, and it needs a task-specific evaluation rather than a throughput run
- Intermediate settings — the template exposes on and off, and nothing was tried between
- Whether the truncation at `max_tokens` 512 would disappear at a larger budget, and what
  that would do to the comparison
