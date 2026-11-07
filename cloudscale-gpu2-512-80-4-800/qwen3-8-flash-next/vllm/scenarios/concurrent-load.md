# Scenario: concurrent load — vLLM TP=4

The `v1` ladder from 1 to 256 parallel clients, both thinking arms, plus the mixed-traffic
run at 32.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md) · `Qwen3.8-Flash-Next-FP8` ·
[the four-card machine](../../../README.md) · measured 2026-11-06

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md), no
deviations: `max_tokens 512`, 40 s per level, 3 warmup requests discarded, tokens from
`usage`. KV pool 3,613,443 tokens, so no level is bounded by cache: 256 requests with
1.3k prompt and 512 answer need under 500,000 tokens.

## Result, thinking on (default)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.55 | 110.3 | 804.9 | 1.79 s | 2.29 s | 99 % × 4 |
| 8 | 2.15 | 446.6 | 3162.1 | 3.67 s | 5.46 s | 97 % × 4 |
| 16 | 3.12 | 654.2 | 4601.1 | 5.15 s | 8.02 s | 100 % × 4 |
| 32 | 4.28 | 893.5 | 6292.8 | 7.55 s | 11.90 s | 100 % × 4 |
| 64 | 5.92 | 1220.9 | 8704.1 | 11.29 s | 17.94 s | 100 % × 4 |
| 128 | 7.88 | 1623.4 | 11569.5 | 17.55 s | 29.59 s | 100 % × 4 |
| 256 | 11.38 | **2274.9** | 16641.5 | 25.73 s | 42.92 s | 100 % × 4 |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.55 | 110.3 | — |
| 8 | 2.15 | 446.6 | — |
| 16 | 3.11 | 651.4 | — |
| 32 | 4.24 | 884.8 | 1.01× |
| 64 | 5.67 | 1,169 | 1.04× |
| 128 | 7.29 | 1,503 | 1.08× |
| 256 | 9.95 | 1,989 | 1.14× |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 4.33 | 877.5 | 6340.0 | 7.62 s | 11.52 s |
| mixed | 2.40 | 1181.5 | 3092.8 | 17.73 s | 17.99 s |

## Result, thinking off

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · chat_template_kwargs: {"enable_thinking": false} -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 2.00 | 98.5 | 2544.5 | 0.50 s | 0.61 s | 98 % × 4 |
| 8 | 6.33 | 318.1 | 8053.6 | 1.25 s | 1.68 s | 100 % × 4 |
| 16 | 8.18 | 413.3 | 10411.3 | 1.90 s | 2.60 s | 100 % × 4 |
| 32 | 10.68 | 530.1 | 13585.6 | 3.00 s | 4.15 s | 100 % × 4 |
| 64 | 13.43 | 666.0 | 17084.8 | 4.80 s | 6.90 s | 100 % × 4 |
| 128 | 15.95 | 799.0 | 20305.8 | 8.17 s | 12.71 s | 100 % × 4 |
| 256 | **18.65** | 928.8 | 23737.7 | 14.20 s | 24.18 s | 100 % × 4 |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 2.00 | 98.5 | — |
| 8 | 6.33 | 318.1 | — |
| 16 | 8.18 | 413.3 | — |
| 32 | 10.67 | 529.4 | — |
| 64 | 13.33 | 661.2 | 1.01× |
| 128 | 15.67 | 784.8 | 1.02× |
| 256 | 18.03 | 897.8 | 1.03× |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 10.60 | 521.6 | 13485.4 | 3.02 s | 4.00 s |
| mixed | 2.80 | 1142.3 | 3624.7 | 15.75 s | 18.18 s |

## Reading it

**2,275 output tok/s at C=256 with thinking on, still rising.** Every doubling of clients
adds 30–40 % of throughput; the ladder has not flattened at 256, and the KV pool would
take seven times more. With thinking off the answers are 50 tokens, so the ladder is
request-bound: 18.65 answers/s at C=256 (24 k total tok/s, most of it prompt).

**The mixed run is the one that tells you about agents.** At C=32 the mix produces more
output tokens per second than the uniform prompt (1,182 against 878) but answers at half
the rate with a 17.7 s p50, because one of the five shapes is a 180-paragraph analysis.
Latency under agent traffic is set by the longest prompt in flight, not by the average.

## With the MTP head

Thinking on only, same protocol, the container restarted with
`--speculative-config '{"method":"qwen4_exp_mtp","num_speculative_tokens":2}'`
([single-stream](single-stream.md#with-the-mtp-head---speculative-config-qwen4_exp_mtp-2-draft-tokens)):

<!-- 2026-11-06T11:55:07+00:00 · vLLM 0.33.0 Docker TP=4 + MTP draft (qwen4_exp_mtp, 2 tokens) · concurrent-load · thinking ON (default) -->

| Concurrent | Answers/s | Output tok/s | vs. no draft | Latency p50 | p95 |
|---|---|---|---|---|---|
| 1 | 0.82 | **174.0** | +58 % | 1.21 s | 1.64 s |
| 8 | 2.52 | 517.3 | +16 % | 3.07 s | 4.68 s |
| 16 | 3.55 | 722.0 | +10 % | 4.51 s | 6.74 s |
| 32 | 4.60 | 979.5 | +10 % | 6.88 s | 11.45 s |
| 64 | 6.88 | 1387.9 | +14 % | 9.66 s | 15.65 s |
| 128 | 8.80 | 1772.2 | +9 % | 15.77 s | 25.36 s |
| 256 | 11.05 | 2235.2 | −2 % | 27.38 s | 43.33 s |
| mixed at 32 | 2.40 | 1169.6 | −1 % | 16.51 s | 20.46 s |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.82 | 174.0 | — |
| 8 | 2.52 | 517.3 | — |
| 16 | 3.55 | 721.5 | — |
| 32 | 4.60 | 979.5 | — |
| 64 | 6.63 | 1,337 | 1.04× |
| 128 | 8.12 | 1,635 | 1.08× |
| 256 | 9.35 | 1,891 | 1.18× |

**The draft pays for the first few clients and is neutral at saturation**: +58 % alone,
+10–16 % up to C=128, nothing at C=256, where every step is already batch-bound. Serving
agents or a handful of users: switch it on. Serving hundreds: it does not matter.

## Against the two-card machines

| Output tok/s, thinking on | C=8 | C=16 | C=32 | C=256 |
|---|---|---|---|---|
| **this**, vLLM FP8, 4× RTX PRO 6000 | 446.6 | 654.2 | 893.5 | **2274.9** |
| Rocky 2× RTX PRO 4500, Strata IQ3_S, 2× RTX PRO 4500, 8 slots | 346.0 | 391.0 | queue | queue |
| Rocky 2× RTX PRO 4500, vLLM 27B FP8 TP=2 | 259.5 | 431.1 | — | 1672.1 |

Strata's eight slots hold their own up to C=8 on one sixth of the VRAM; above that
only a KV pool like this one carries the load.
