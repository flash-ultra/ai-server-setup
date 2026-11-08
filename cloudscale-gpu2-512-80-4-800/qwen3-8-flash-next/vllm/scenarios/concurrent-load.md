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

**1,989 output tok/s at C=256 with thinking on, over the real run time.** Up to 256 every
doubling of clients adds 29–36 % of throughput; [above 256](#above-256-clients) the curve flattens
(2,481 at 1,024), although the KV pool would take seven times more. With thinking off the answers are 50 tokens, so the ladder is
request-bound: 18.0 answers/s at C=256 (24 k total tok/s measured, most of it prompt).

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
+9–16 % up to C=128 and 5 % less at C=256 over the real run time, where every step is
already batch-bound. Serving
agents or a handful of users: switch it on. Serving hundreds: it does not matter.

## Against the two-card machines

| Output tok/s as measured (`v1`), thinking on | C=8 | C=16 | C=32 | C=256 |
|---|---|---|---|---|
| **this**, vLLM FP8, 4× RTX PRO 6000 | 446.6 | 654.2 | 893.5 | **2274.9** |
| Rocky 2× RTX PRO 4500, Strata IQ3_S, 2× RTX PRO 4500, 8 slots | 346.0 | 391.0 | queue | queue |
| Rocky 2× RTX PRO 4500, vLLM 27B FP8 TP=2 | 259.5 | 431.1 | — | 1672.1 |

Strata's eight slots hold their own up to C=8 on one sixth of the VRAM; above that
only a KV pool like this one carries the load.

## Above 256 clients

Measured 2026-11-08 with the same server flags, levels 256 to 1024 (a documented deviation, for
the comparison with [DeepSeek-V4-Flash-0731](../../../deepseek-v4-flash-0731/vllm/scenarios/concurrent-load.md),
which keeps climbing there). `bench.py` now also prints the wall-clock time and concurrency ÷
mean latency.

<!-- protocol v1 · DEVIATION levels 256,384,512,768,1024 · otherwise as above -->

**Thinking on**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 11.25 | 2268.2 | 16476.9 | 26.95 s | 42.96 s | 98 % · 99 % · 98 % · 98 % |
| 384 | 11.95 | 2439.2 | 17532.0 | 41.70 s | 49.82 s | 100 % · 100 % · 100 % · 100 % |
| 512 | 13.00 | 2673.6 | 19092.6 | 48.57 s | 54.36 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 19.20 | 3948.1 | 28197.7 | 69.02 s | 76.10 s | 100 % · 100 % · 100 % · 100 % |
| 1024 | 25.60 | 5345.3 | 37678.1 | 86.19 s | 101.90 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 9.50 | 1,915 | 1.18× |
| 384 | 9.21 | 1,880 | 1.30× |
| 512 | 10.54 | 2,168 | 1.23× |
| 768 | 11.13 | 2,288 | 1.73× |
| 1024 | 11.88 | 2,481 | 2.15× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 56.3 s | 8.00 | 1612.4 | 27.81 s | 9.20 answers/s |
| 384 | 56.3 s | 8.50 | 1734.1 | 37.44 s | 10.26 answers/s |
| 512 | 58.5 s | 8.90 | 1829.6 | 47.89 s | 10.69 answers/s |
| 768 | 80.9 s | 9.49 | 1952.2 | 68.61 s | 11.19 answers/s |
| 1024 | 107.4 s | 9.54 | 1991.5 | 85.04 s | 12.04 answers/s |

**Thinking off**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 18.55 | 937.8 | 23624.4 | 14.22 s | 23.57 s | 100 % · 100 % · 100 % · 100 % |
| 384 | 19.23 | 962.6 | 24474.8 | 20.49 s | 36.49 s | 100 % · 100 % · 100 % · 100 % |
| 512 | 20.52 | 1022.4 | 26124.4 | 29.78 s | 42.72 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 20.85 | 1039.2 | 26538.7 | 43.66 s | 45.61 s | 100 % · 100 % · 100 % · 100 % |
| 1024 | 27.15 | 1345.3 | 34549.8 | 55.84 s | 59.32 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 18.00 | 910.1 | 1.03× |
| 384 | 18.74 | 938.1 | 1.03× |
| 512 | 17.19 | 856.6 | 1.19× |
| 768 | 17.59 | 876.7 | 1.19× |
| 1024 | 18.34 | 908.7 | 1.48× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 44.6 s | 16.65 | 841.6 | 14.52 s | 17.62 answers/s |
| 384 | 44.6 s | 17.26 | 864.2 | 21.09 s | 18.20 answers/s |
| 512 | 46.7 s | 17.59 | 876.2 | 27.36 s | 18.72 answers/s |
| 768 | 46.7 s | 17.87 | 890.4 | 40.53 s | 18.95 answers/s |
| 1024 | 61.5 s | 17.65 | 874.8 | 51.43 s | 19.91 answers/s |

**The curve flattens above 256.** Over the real run time 1,915 tok/s at 256 in this rerun and
2,481 at 1,024, while the median latency rises from 27 to 86 s; by mean latency 2,514. Without
thinking it stays at 17–19 answers/s from 256 on. Here `v1` reads high by up to 2.15×: at 86 s
per answer each client's one request is counted against a 40 s window.
