# Scenario: concurrent load — vLLM TP=2

The full protocol ladder, both thinking arms, plus the mixed-traffic run.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `Qwen3.8-27B` BF16 ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-24

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations — levels 1/8/16/32/64/
128/256, `max_tokens` 512, 40 s per level, 3 warmup requests discarded, counted via
`usage`. `bench.py --scenario concurrent`, against the engine on `127.0.0.1:8001`
directly, not through the `api-router`.

The thinking-off arm adds `--chat-template-kwargs '{"enable_thinking": false}'`, which
was [verified to work](../README.md#thinking-is-on-by-default-and-two-of-four-switches-work)
before the run. The embedding model stayed loaded; see
[single stream](single-stream.md#method).

**One run per arm.** DeepSeek's ladder states a ≤ 5 % run-to-run spread from three
runs; this is a single pass per arm.

## Result, thinking on (default)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.28 | 52.6 | 399.9 | 3.80 s | 5.41 s | 100 % · 100 % |
| 8 | 1.73 | 342.2 | 2520.8 | 4.93 s | 7.26 s | 100 % · 100 % |
| 16 | 2.98 | 579.4 | 4336.8 | 5.66 s | 7.28 s | 100 % · 100 % |
| 32 | 4.72 | 943.1 | 6910.8 | 7.04 s | 10.12 s | 100 % · 100 % |
| 64 | 6.50 | 1275.3 | 9484.9 | 10.28 s | 15.43 s | 100 % · 100 % |
| 128 | 7.97 | 1564.0 | 11636.4 | 17.41 s | 27.86 s | 100 % · 100 % |
| 256 | **9.43** | **1821.0** | 13724.8 | 34.89 s | 45.22 s | 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.26 | 49.4 | 1.06× |
| 8 | 1.62 | 321.0 | 1.07× |
| 16 | 2.83 | 549.6 | 1.05× |
| 32 | 4.55 | 908.2 | 1.04× |
| 64 | 6.23 | 1,221 | 1.04× |
| 128 | 7.35 | 1,443 | 1.08× |
| 256 | 7.34 | 1,417 | 1.29× |

## Result, thinking off

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · chat_template_kwargs: {"enable_thinking": false} -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.85 | 45.2 | 1084.8 | 1.13 s | 1.51 s | 100 % · 100 % |
| 8 | 4.75 | 249.2 | 6058.5 | 1.67 s | 2.21 s | 100 % · 100 % |
| 16 | 7.33 | 390.6 | 9349.1 | 2.18 s | 3.00 s | 100 % · 100 % |
| 32 | 9.88 | 524.9 | 12602.0 | 3.19 s | 4.62 s | 100 % · 100 % |
| 64 | 11.80 | 631.2 | 15062.6 | 5.41 s | 8.15 s | 100 % · 100 % |
| 128 | 12.60 | 677.4 | 16087.2 | 10.22 s | 16.60 s | 100 % · 100 % |
| 256 | **13.45** | 718.0 | 17167.4 | 19.94 s | 34.81 s | 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.85 | 45.2 | — |
| 8 | 4.75 | 249.2 | — |
| 16 | 7.33 | 390.6 | — |
| 32 | 9.88 | 524.9 | — |
| 64 | 11.80 | 631.2 | — |
| 128 | 12.52 | 673.3 | 1.01× |
| 256 | 12.84 | 685.4 | 1.05× |

## Prompt mix at concurrency 32

| Thinking | Traffic | Answers/s | Output tok/s | Total tok/s | p50 | p95 |
|---|---|---|---|---|---|---|
| on | uniform | 4.80 | 925.1 | 6987.5 | 6.93 s | 10.28 s |
| on | mixed | 2.55 | 1219.3 | 3331.0 | 14.84 s | 15.59 s |
| off | uniform | 9.90 | 527.3 | 12635.0 | 3.23 s | 4.59 s |
| off | mixed | 2.90 | 1248.4 | 3825.1 | 14.50 s | 15.26 s |

**Mixed traffic halves the answer rate and doubles the token rate**, in both arms. The
mix contains long-analysis and code-review shapes that generate to the 512-token cap, so
answers get longer and rarer. Note that the two arms nearly converge under the mix —
2.55 against 2.90 answers/s, 1219 against 1248 output tok/s — because a request that
runs to the cap spends its budget there whether or not it was thinking.

## Reading

**Both cards report 100 % at every level including concurrency 1**, which is unlike
every other setup in this repository. The sparse models here idle one card at low
concurrency and climb into the nineties only under load; this one is bandwidth-saturated
from the first request. The utilisation column therefore carries no information about
headroom for this model — the throughput curve does.

**Both ladders have flattened by 256.** Over the real run time the thinking-on arm holds
7.35 → 7.34 answers/s from 128 to 256 and the thinking-off arm gains 3 %; the 18 % the
measured figures showed for thinking on was the
[measurement window](../../../../benchmark/README.md#the-window-overstates-slow-answers).
Neither arm was taken past 256.

**The two arms cross, and which one leads depends on the column.** Over the real run time thinking
off gives 1.75× the answers; thinking on gives 2.07× the output tokens. Tokens per answer is 193
against 53. This is the same shape as every other reasoning model measured here, and it
is why a row without a stated thinking arm cannot be compared to anything.

**Latency is where the arms differ most at the top.** 34.89 s against 19.94 s at p50,
and 45.22 against 34.81 at p95. For an interactive workload the ladder runs out long
before 256 in either arm.

## Against DeepSeek-V4-Flash-0731

Same machine, same protocol, both arms stated —
[its own file](../../../deepseek-v4-flash-0731/sglang/scenarios/concurrent-load.md):

| at concurrency 256 | Qwen **on** | DS **on** | Qwen **off** | DS **off** |
|---|---|---|---|---|
| Answers/s, over the real run time | 7.34 | **9.28** | 12.84 | **32.16–32.20** |
| Output tok/s, over the real run time | 1,417 | **3,032** | 685 | **1,158–1,166** |
| Latency p50 | 34.89 s | **27.58 s** | 19.94 s | **7.95–7.96 s** |
| Tokens per answer | 193 | 327 | 53 | 35–36 |

**DeepSeek wins every cell**, by 0.79× to 0.40× depending on arm and column. The widest
gap is answers per second with thinking off — 12.8 against 32.2, a factor of 2.5 — and
the narrowest is answers per second with thinking on, where the two are within 21 %.

**The gap narrows as answers get longer**, which is the signature of the architectural
difference rather than of tuning. Thinking-on answers are long enough that both setups
spend most of their time decoding, and there Qwen's handicap is one factor: it reads
25.9 GiB of weights per token against a fraction of DeepSeek's 284 B. Short answers add
a second handicap on top, because prefill is also slower — see
[long context](long-context.md).

**This is the cost side of the [quality result](quality.md).** The same two setups, the
same two days: Qwen answers better and DeepSeek answers faster, and neither margin is
small enough to ignore or large enough to settle the question alone.
