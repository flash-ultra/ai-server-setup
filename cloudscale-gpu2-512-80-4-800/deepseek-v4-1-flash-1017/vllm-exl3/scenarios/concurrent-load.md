# Scenario: concurrent load — EXL3 on four cards

**Setup:** [pack recipe, `PROFILE=8x REPLICA=0`, 128 sequences, NCCL all-reduce](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07

## Method

Protocol [`v1`](../../../../benchmark/README.md), full ladder 1 to 256, both thinking arms,
no deviations. The profile admits 128 sequences, so 256 queues half its clients.

## Result, thinking on (default)

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.97 | 158.5 | 1367.5 | 0.98 s | 1.47 s | 97–99 % |
| 8 | 2.75 | **467.2** | 3877.2 | 2.88 s | 4.58 s | 91–98 % |
| 16 | 4.15 | **682.4** | 5828.4 | 3.91 s | 5.85 s | 88–97 % |
| 32 | 4.08 | 676.8 | 5729.8 | 5.99 s | 19.53 s | 68–72 % |
| 64 | 7.25 | 1201.2 | 10191.2 | 9.32 s | 13.81 s | 93–94 % |
| 128 | 8.00 | 1309.9 | 11229.9 | 16.24 s | 31.87 s | 77–81 % |
| 256 | **12.85** | **2111.8** | 18045.8 | 27.87 s | 37.19 s | 92–94 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.97 | 158.5 | — |
| 8 | 2.75 | 467.2 | — |
| 16 | 4.09 | 672.9 | 1.01× |
| 32 | 4.08 | 676.8 | — |
| 64 | 6.87 | 1,138 | 1.06× |
| 128 | 7.88 | 1,291 | 1.01× |
| 256 | 9.19 | 1,510 | 1.40× |

**Prompt mix at concurrency 32:** uniform 5.85 answers/s, 967.6 tok/s, p50 5.53 s · mixed
2.58 answers/s, 1194.0 tok/s, p50 15.47 s.

## Result, thinking off

<!-- protocol v1 · chat_template_kwargs: {"enable_thinking": false} -->

| Concurrent | Answers/s | Output tok/s | Latency p50 | p95 |
|---|---|---|---|---|
| 1 | 2.15 | 118.3 | 0.47 s | 0.57 s |
| 8 | 5.38 | 290.0 | 1.51 s | 2.05 s |
| 16 | 7.75 | 434.3 | 2.14 s | 2.79 s |
| 32 | 10.82 | 586.5 | 3.11 s | 4.12 s |
| 64 | 14.97 | 805.8 | 4.41 s | 6.09 s |
| 128 | 16.25 | 881.7 | 7.34 s | 15.06 s |
| 256 | **22.95** | 1247.8 | 13.14 s | 16.48 s |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 2.13 | 117.1 | 1.01× |
| 8 | 5.30 | 285.6 | 1.02× |
| 16 | 7.48 | 419.0 | 1.04× |
| 32 | 10.29 | 557.7 | 1.05× |
| 64 | 14.51 | 781.2 | 1.03× |
| 128 | 16.25 | 881.7 | — |
| 256 | 19.48 | 1,059 | 1.18× |

**Prompt mix at concurrency 32:** uniform 10.97 answers/s, p50 3.02 s · mixed 3.02 answers/s, p50 12.39 s.

## Reading it

**Four cards give this pack 1.8–3.8× under load**, against 1.2× for MiMo on the same
step: 467 against 261 tok/s at C=8, 673 against 254 at C=16, 1,510 against 399 at C=256,
all over the real run time.
The two-card configuration runs 8 sequences by default and 32 at most; four cards hold the
whole expert set in VRAM and admit 128. **C=32 does not gain over C=16** (677 against 673 tok/s, the
cards at 68–72 %, p95 three times p50), and C=128 runs the cards at 77–81 %: the drafter's
verify batches and the NCCL all-reduce do not fill the cards at those sizes; one run per level,
so the flat spot is worth re-measuring before it is read as a property.

| Output tok/s over the real run time, thinking on | C=1 | C=8 | C=16 | C=256 |
|---|---|---|---|---|
| **DeepSeek EXL3, 4 cards** | 158.5 | 467.2 | 672.9 | 1,510 |
| DeepSeek EXL3, 2 cards | 140.3 | 261.0 | 253.5 | 399 |
| DeepSeek GSQ-RCO, Strata, 4 cards, 2 replicas | 106.7 | 302.1 | 282.3 | — |
| Qwen3.8-Flash-Next FP8, vLLM, 4 cards | 110.3 | 446.6 | 651.4 | 1,989 |
| MiMo-V2.6-Flash-RL, vLLM, 4 cards | 139.3 | 465.2 | 660.6 | 3,650 |
