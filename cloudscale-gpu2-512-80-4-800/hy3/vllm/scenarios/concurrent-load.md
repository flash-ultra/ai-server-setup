# Scenario: concurrent load — Hy3, TP=4

**Setup:** [vLLM 0.33.0 TP=4, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 20:43–21:01

Protocol [`v1`](../../../../benchmark/README.md), full ladder, both arms: `reasoning_effort: high`, which
this server sets as its default, and `no_think`, the template's own default.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

**Thinking on (`reasoning_effort: high`)**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.17 | 89.6 | 303.6 | 6.02 s | 6.02 s | 99 % · 99 % · 99 % · 99 % |
| 8 | 0.80 | 409.5 | 1387.9 | 12.38 s | 12.47 s | 99 % · 99 % · 99 % · 99 % |
| 16 | 1.20 | 614.1 | 2081.7 | 17.44 s | 17.48 s | 99 % · 99 % · 99 % · 99 % |
| 32 | 1.60 | 818.8 | 2775.6 | 24.57 s | 24.63 s | 100 % · 100 % · 100 % · 100 % |
| 64 | 3.20 | 1636.8 | 5550.4 | 36.53 s | 36.60 s | 100 % · 100 % · 100 % · 100 % |
| 128 | 6.40 | 3258.7 | 11085.9 | 37.72 s | 37.93 s | 100 % · 100 % · 100 % · 100 % |
| 256 | 6.40 | 3270.7 | 11097.9 | 58.05 s | 58.18 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.17 | 87.6 | 1.02× |
| 8 | 0.65 | 330.8 | 1.24× |
| 16 | 0.92 | 469.5 | 1.31× |
| 32 | 1.30 | 666.5 | 1.23× |
| 64 | 1.75 | 896.1 | 1.83× |
| 128 | 3.39 | 1,728 | 1.89× |
| 256 | 4.41 | 2,254 | 1.45× |

**Prompt mix at concurrency 32:** uniform 1.60 answers/s, 819.2 tok/s, p50 25.95 s · mixed 1.60 answers/s, 819.2 tok/s, p50 27.93 s.

**Thinking off (`no_think`)**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 1.48 | 81.5 | 1889.9 | 0.67 s | 0.89 s | 98 % · 99 % · 98 % · 98 % |
| 8 | 5.17 | 305.8 | 6650.4 | 1.48 s | 1.95 s | 99 % · 99 % · 99 % · 99 % |
| 16 | 7.50 | 434.9 | 9629.9 | 2.09 s | 2.78 s | 99 % · 99 % · 99 % · 99 % |
| 32 | 10.70 | 618.8 | 13737.0 | 2.94 s | 3.94 s | 100 % · 100 % · 100 % · 100 % |
| 64 | 14.45 | 834.5 | 18550.2 | 4.51 s | 6.11 s | 100 % · 100 % · 100 % · 100 % |
| 128 | 28.98 | 1692.8 | 37216.2 | 4.44 s | 6.00 s | 100 % · 100 % · 100 % · 100 % |
| 256 | 40.20 | 2333.3 | 51618.5 | 6.40 s | 8.77 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 1.48 | 81.5 | — |
| 8 | 5.17 | 305.8 | — |
| 16 | 7.50 | 434.9 | — |
| 32 | 10.70 | 618.8 | — |
| 64 | 14.19 | 819.5 | 1.02× |
| 128 | 28.83 | 1,684 | 1.01× |
| 256 | 40.00 | 2,322 | 1.01× |

**Prompt mix at concurrency 32:** uniform 10.45 answers/s, 611.9 tok/s, p50 2.97 s · mixed 2.15 answers/s, 735.0 tok/s, p50 19.82 s.

**With thinking on, every answer stops at the 512-token cap:** output ÷ answers is 512 at every
level, so at `high` this arm measures decode under load and no finished answer. Over the real
run time the cards deliver 2,254 tok/s at 256 clients, between Nemotron-3-Super (2,408) and
Qwen3.8-Flash-Next FP8 (1,989). From 64 to 128 clients the rate doubles at unchanged latency,
the same step MiMo and Beam showed under this vLLM.

**Without thinking the answers are 58 tokens long and prefill does the work:** 40 answers/s
at 256 clients with a median of 6.4 s, 51.6 k tok/s counted with the prompts.
