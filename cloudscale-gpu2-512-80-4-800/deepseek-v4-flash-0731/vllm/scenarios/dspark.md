# Scenario: DSpark — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md) plus
`--speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'`
· [the four-card machine](../../../README.md) · measured 2026-11-08, 01:50–02:07

The 0731 checkpoint carries its own draft module; k=7 with probabilistic draft sampling is the
vLLM recipe's setting, and the stock 0.33 image runs it on sm120 without the FlashInfer upgrade
the recipe asked for in August. Protocol [`v1`](../../../../benchmark/README.md): single stream,
full ladder and decode, both arms. Probabilistic draft sampling leaves the output distribution
unchanged; `q1` was not repeated for this configuration.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Single stream | thinking on, DSpark | thinking on, no draft | `thinking: false`, DSpark | `thinking: false`, no draft |
|---|---|---|---|---|
| Output | **169.8 tok/s** | 95.3 | **115.5** | 80.7 |
| Over the wall-clock time | 164.0 tok/s | 90.1 | 114.2 | 80.2 |
| Latency p50 | 1.04 s | 2.59 s | 0.31 s | 0.44 s |
| Tokens per answer | 206 (82 % reasoning) | 254 | 37 | 36 |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 165 / 338 | 0.06 / 0.05 s | **167.8 / 155.1 tok/s** |
| thinking off, run 1 / 2 | 197 / 168 | 0.05 / 0.05 s | **209.4 / 186.3 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.23 / 0.05 s | **290.1 / 320.2 tok/s** |
| behind a 64k prompt | 292 | 9.42 s | **183.4 tok/s** |

**Ladder, thinking on**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.78 | 166.7 | 1168.7 | 1.11 s | 2.43 s | 99 % · 99 % · 99 % · 99 % |
| 8 | 2.23 | 514.9 | 3391.8 | 3.43 s | 6.62 s | 95 % · 94 % · 95 % · 94 % |
| 16 | 4.70 | 940.4 | 7017.5 | 3.16 s | 7.20 s | 93 % · 94 % · 94 % · 94 % |
| 32 | 6.95 | 1378.8 | 10365.2 | 4.28 s | 8.83 s | 100 % · 100 % · 100 % · 100 % |
| 64 | 8.15 | 1609.1 | 12147.0 | 7.63 s | 15.18 s | 89 % · 88 % · 89 % · 88 % |
| 128 | 10.70 | 2125.4 | 15960.5 | 14.77 s | 25.79 s | 89 % · 87 % · 88 % · 88 % |
| 256 | 12.07 | 2426.3 | 18039.3 | 32.28 s | 59.96 s | 63 % · 64 % · 63 % · 63 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.78 | 166.7 | — |
| 8 | 2.23 | 514.9 | — |
| 16 | 4.70 | 940.4 | — |
| 32 | 6.95 | 1,379 | — |
| 64 | 8.15 | 1,609 | — |
| 128 | 8.67 | 1,721 | 1.23× |
| 256 | 7.93 | 1,594 | 1.52× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 42.6 s | 0.73 | 156.4 | 1.35 s | 0.74 answers/s |
| 8 | 43.8 s | 2.03 | 470.7 | 3.75 s | 2.14 answers/s |
| 16 | 46.9 s | 4.00 | 801.2 | 3.69 s | 4.34 answers/s |
| 32 | 44.8 s | 6.20 | 1230.7 | 4.86 s | 6.59 answers/s |
| 64 | 47.0 s | 6.94 | 1369.7 | 8.48 s | 7.54 answers/s |
| 128 | 59.8 s | 7.16 | 1422.7 | 15.21 s | 8.41 answers/s |
| 256 | 79.8 s | 6.05 | 1216.2 | 33.84 s | 7.56 answers/s |

**Prompt mix at concurrency 32:** uniform 6.80 answers/s, 1,401.9 tok/s, p50 4.43 s · mixed 2.95 answers/s, 1,274.0 tok/s, p50 13.23 s.

**Ladder, thinking off**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 3.17 | 114.2 | 3968.7 | 0.31 s | 0.43 s | 99 % · 99 % · 99 % · 99 % |
| 8 | 9.12 | 341.7 | 11419.5 | 0.85 s | 1.24 s | 100 % · 100 % · 100 % · 100 % |
| 16 | 12.97 | 479.4 | 16231.0 | 1.20 s | 1.75 s | 100 % · 100 % · 100 % · 100 % |
| 32 | 16.40 | 604.4 | 20514.0 | 1.93 s | 2.91 s | 100 % · 97 % · 100 % · 98 % |
| 64 | 20.40 | 747.6 | 25513.2 | 3.10 s | 4.49 s | 100 % · 100 % · 100 % · 100 % |
| 128 | 22.27 | 821.4 | 27863.3 | 5.89 s | 8.77 s | 100 % · 100 % · 100 % · 100 % |
| 256 | 23.38 | 864.3 | 29241.6 | 11.43 s | 18.28 s | 93 % · 93 % · 93 % · 93 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 3.17 | 114.2 | — |
| 8 | 9.12 | 341.7 | — |
| 16 | 12.97 | 479.4 | — |
| 32 | 16.40 | 604.4 | — |
| 64 | 20.40 | 747.6 | — |
| 128 | 21.73 | 801.5 | 1.02× |
| 256 | 22.40 | 828.0 | 1.04× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 40.5 s | 3.14 | 112.8 | 0.32 s | 3.17 answers/s |
| 8 | 40.6 s | 8.99 | 336.7 | 0.89 s | 9.04 answers/s |
| 16 | 41.6 s | 12.49 | 461.5 | 1.25 s | 12.83 answers/s |
| 32 | 41.6 s | 15.78 | 581.4 | 1.98 s | 16.17 answers/s |
| 64 | 42.7 s | 19.11 | 700.2 | 3.22 s | 19.88 answers/s |
| 128 | 43.9 s | 20.30 | 748.5 | 6.01 s | 21.29 answers/s |
| 256 | 47.1 s | 19.87 | 734.6 | 12.01 s | 21.31 answers/s |

**Prompt mix at concurrency 32:** uniform 16.73 answers/s, 617.1 tok/s, p50 1.88 s · mixed 3.83 answers/s, 1,356.8 tok/s, p50 10.28 s.

## Reading

**DSpark nearly doubles the single stream:** 169.8 against 95.3 tok/s with thinking, 115.5
against 80.7 without. On a 1,500-token answer decode reaches 290–320 tok/s, with a mean
acceptance length of 6.8 drafted tokens; on the short protocol answers it was 3.2–3.4. Behind a
64k prompt it still decodes at 183 tok/s, twice the engine without a draft.

**Up to 64 clients it stays ahead, from 128 it falls behind.** Over the real run time, thinking on:

| Concurrent | no draft | DSpark |
|---|---|---|
| 1 | 93 tok/s | **167** |
| 16 | 690 | **940** |
| 32 | 1,026 | **1,379** |
| 64 | 1,507 | **1,609** |
| 128 | **2,838** | 1,721 |
| 256 | **3,869** | 1,594 — cards at 63 % |

**For a handful of users DSpark, for a crowd the engine without it.** The flag is set at start,
so one server is either the one or the other.
