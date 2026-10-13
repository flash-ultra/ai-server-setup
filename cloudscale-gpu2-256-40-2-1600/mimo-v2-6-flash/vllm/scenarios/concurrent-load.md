# Scenario: concurrent load — vLLM, MiMo build

The full concurrency sweep.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13

## Method

Protocol `v1`, `--scenario concurrent`, no deviations. Thinking **on**, the default of this
checkpoint. Served context 49,152 tokens.

**This setup serves a smaller window than the others on this machine** — 49,152 against
262,144 for DeepSeek-0731 and 196,608 for MiniMax. A smaller window means smaller
activation buffers and more room for the batch, so the comparison below is not
configuration-neutral. It is the largest window this checkpoint was measured at; see
[still open](../README.md#still-open).

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 1.77 | 113.4 | 2,275.3 | 0.55 s | 0.71 s | 100 % · 100 % |
| 8 | 4.95 | 329.5 | 6,358.6 | 1.62 s | 2.21 s | 100 % · 100 % |
| 16 | 6.97 | 472.4 | 8,967.9 | 2.25 s | 3.14 s | 100 % · 100 % |
| 32 | 10.50 | 703.6 | 13,492.6 | 3.11 s | 4.21 s | 100 % · 100 % |
| 64 | 16.88 | 1,144.8 | 21,698.6 | 3.81 s | 5.21 s | 100 % · 100 % |
| 128 | 28.35 | 1,919.8 | 36,450.1 | 4.61 s | 6.29 s | 100 % · 100 % |
| 256 | **46.10** | **3,115.6** | 59,265.4 | **5.71 s** | 7.98 s | 100 % · 100 % |

A partial earlier run at levels 1, 8, 16, 32, 64 reproduced these figures to within 2 %
(1.75 / 4.85 / 6.97 / 10.50 / 17.15 answers/s).

Mix at concurrency 32: uniform 10.32 answers/s · 694.0 output tok/s · p50 3.14 s.

## Reading

**It leads the machine on answers and latency, against either arm of the production
model.** DeepSeek-0731 appears twice below because it was measured both ways, and a
comparison against only one of its arms would be picking the convenient one:

| at concurrency 256 | MiMo | [DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/concurrent-load.md) | DeepSeek-0731 | [MiniMax-M2.5](../../../minimax-m2-5/vllm/scenarios/concurrent-load.md) |
|---|---|---|---|---|
| Thinking | **on** | **on** | off (default) | on, not switchable |
| Answers/s | **46.10** | 10.97 | 32.58 | 9.75 |
| Output tok/s | 3,115.6 | **3,583.8** | 1,173.2 | 2,947.3 |
| Latency p50 | **5.71 s** | 27.58 s | 7.96 s | 57.34 s |
| Tokens/answer | 68 | 327 | 35 | 258 |

**Against the like-for-like arm — both thinking — it is 4.2× the answers at a fifth of the
latency.** DeepSeek stays ahead on output tokens per second, and the tokens-per-answer
column says why: 327 against 68. It is not delivering more answers, it is writing five
times as much per answer, four fifths of which is scratchpad the user never sees.

**Both cards at 100 % from the first level to the last.** MiniMax-M2.5 is the only other
setup here that does that — and it does it at a fifth of the answer rate. Saturation says
the engine is never idling; it says nothing about how much work comes out. DeepSeek runs
91–99 % and delivers 3.3× MiniMax's answers; llama.cpp pins in the forties.

**The curve had not turned over at 256.** Answers per second rose monotonically through
every level and the median response was still under six seconds at the top. Where it
flattens is unmeasured.

**One thing qualifies all of this: MiMo serves a fifth of the context window** — 49,152
against 262,144 — which is part of why its batch fits.

## Not measured

- **Levels above 256**, where the curve was still rising.
- **A second full run.** The partial earlier run covers levels 1–64 only.
- **The mixed-traffic arm** beyond the uniform row.
