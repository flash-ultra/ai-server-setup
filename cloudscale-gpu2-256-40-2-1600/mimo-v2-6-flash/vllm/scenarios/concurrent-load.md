# Scenario: concurrent load — vLLM, MiMo build

The full concurrency sweep.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13

## Method

Protocol `v1`, `--scenario concurrent`, no deviations. Thinking **on**, the default of this
checkpoint. Served context 196,608 tokens — the same window as MiniMax-M2.5 on this
machine, against 262,144 for DeepSeek-0731.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 1.77 | 114.8 | 2,276.8 | 0.55 s | 0.72 s | 99 % · 99 % |
| 8 | 4.80 | 322.7 | 6,169.1 | 1.64 s | 2.22 s | 100 % · 100 % |
| 16 | 6.90 | 466.7 | 8,870.9 | 2.28 s | 3.29 s | 100 % · 100 % |
| 32 | 10.35 | 700.6 | 13,307.0 | 3.12 s | 4.32 s | 100 % · 100 % |
| 64 | 17.10 | 1,162.6 | 21,990.4 | 3.81 s | 5.24 s | 100 % · 100 % |
| 128 | 28.80 | 1,929.7 | 37,008.1 | 4.55 s | 6.31 s | 100 % · 100 % |
| 256 | **46.05** | **3,128.9** | 59,217.8 | **5.74 s** | 7.90 s | 100 % · 100 % |

**An earlier series on the same setup at a 49,152 window is indistinguishable:** 46.10
answers/s and 3,115.6 output tok/s at concurrency 256, against 46.05 and 3,128.9 here.
Quadrupling the served window cost 0.1 % of the answer rate. A third, partial run at
levels 1–64 reproduced both to within 2 %.

Traffic mix at concurrency 32:

| Traffic | Answers/s | Output tok/s | Latency p50 | p95 |
|---|---|---|---|---|
| uniform | 10.25 | 695.6 | 3.13 s | 4.29 s |
| mixed | 1.73 | 752.8 | 26.48 s | 29.90 s |

**The mixed arm could not be run at all on the 49,152 window** — its long prompts did not
fit. It is the one place where the larger window changes a measurement rather than
leaving it alone: more tokens per second, a sixth of the answers, and latency up 8×.

## Reading

**It leads the machine on answers and latency, against either arm of the production
model.** DeepSeek-0731 appears twice below because it was measured both ways, and a
comparison against only one of its arms would be picking the convenient one:

| at concurrency 256 | MiMo | [DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/concurrent-load.md) | DeepSeek-0731 | [MiniMax-M2.5](../../../minimax-m2-5/vllm/scenarios/concurrent-load.md) |
|---|---|---|---|---|
| Thinking | **on** | **on** | off (default) | on, not switchable |
| Answers/s | **46.05** | 10.97 | 32.58 | 9.75 |
| Output tok/s | 3,128.9 | **3,583.8** | 1,173.2 | 2,947.3 |
| Latency p50 | **5.74 s** | 27.58 s | 7.96 s | 57.34 s |
| Tokens/answer | 68 | 327 | 35 | 258 |
| Context served | 196,608 | 262,144 | 262,144 | 196,608 |

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

**The window is no longer the caveat it was.** An earlier version of this page noted that
MiMo served a fifth of DeepSeek's context, which made the batch comparison unfair. It now
serves 196,608 — the same as MiniMax, three quarters of DeepSeek — at the same throughput
it had at 49,152. The ranking above does not depend on a smaller window.
