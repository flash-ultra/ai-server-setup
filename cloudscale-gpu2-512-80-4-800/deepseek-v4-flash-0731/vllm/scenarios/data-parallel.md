# Scenario: four copies (DP=4 + EP) — DeepSeek-V4-Flash-0731, vLLM

**Setup:** [vLLM 0.33.0](../README.md) with `--data-parallel-size 4 --enable-expert-parallel` and
**one changed line** · [the four-card machine](../../../README.md) · measured 2026-11-08, 11:25–11:57

## Method

The recipe's `single_node_dep`: four copies of attention, one per card, with the experts spread
over all four. In stock vLLM 0.33 it [fails during graph capture](../README.md#four-copies-need-one-changed-line)
because the workspace for FlashInfer's SM120 sparse-MLA decode is a fixed 128 MiB. A copy of
`vllm/models/deepseek_v4/nvidia/flashinfer_sparse.py` with that constant at 1 GiB, mounted over
the original, is the whole change:

```
_FLASHINFER_DSV4_WORKSPACE_BUFFER_SIZE = 1024 * 1024 * 1024  # 128 MiB in v0.33.0
docker run ... -v ./flashinfer_sparse.py:/usr/local/lib/python3.12/dist-packages/vllm/models/deepseek_v4/nvidia/flashinfer_sparse.py:ro \
  vllm/vllm-openai:v0.33.0 deepseek-ai/DeepSeek-V4-Flash-0731 ... \
  --tensor-parallel-size 1 --data-parallel-size 4 --enable-expert-parallel \
  --compilation-config '{"cudagraph_mode":"FULL_AND_PIECEWISE","custom_ops":["all"]}'
```

All other flags as in the [TP=4 setup](../README.md). Ready after 522 s, 422 s of it engine init;
1,246,493 cache tokens per copy, 4.99 M in all, 87,433 MiB per card. Protocol
[`v1`](../../../../benchmark/README.md) for single stream, ladder and decode, both arms; the levels
384–1024 are the same deviation as on the [TP=4 page](concurrent-load.md). `q1` was not repeated:
the copies compute the same model with the same kernels.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Single stream | four copies | TP=4 |
|---|---|---|
| thinking on | 79.2 tok/s · p50 2.80 s | **95.3** · 2.59 s |
| thinking off | 63.0 tok/s · p50 0.57 s | **80.7** · 0.44 s |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 267 / 183 | 0.06 / 0.09 s | **73.1 / 72.8 tok/s** |
| thinking off, run 1 / 2 | 272 / 156 | 0.06 / 0.05 s | **73.1 / 73.2 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.22 / 0.05 s | **72.1 / 72.1 tok/s** |
| behind a 64k prompt | 91 | 8.34 s | **72.4 tok/s** |

## Ladder to 256

**Thinking on**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.35 | 75.8 | 528.4 | 2.59 s | 4.80 s | 100 % · 100 % · 100 % · 100 % |
| 8 | 1.80 | 389.9 | 2717.2 | 4.48 s | 8.08 s | 100 % · 100 % · 100 % · 100 % |
| 16 | 3.10 | 676.0 | 4684.2 | 5.06 s | 9.62 s | 100 % · 100 % · 100 % · 100 % |
| 32 | 5.33 | 1106.9 | 7992.1 | 5.77 s | 11.83 s | 100 % · 100 % · 100 % · 100 % |
| 64 | 8.78 | 1790.2 | 13136.3 | 6.93 s | 15.12 s | 100 % · 100 % · 100 % · 100 % |
| 128 | 15.35 | 3111.4 | 22959.0 | 8.22 s | 17.27 s | 100 % · 100 % · 100 % · 100 % |
| 256 | 26.70 | 5360.9 | 39884.0 | 9.55 s | 19.15 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 0.35 | 75.8 | — |
| 8 | 1.79 | 386.8 | 1.01× |
| 16 | 3.10 | 676.0 | — |
| 32 | 5.33 | 1,107 | — |
| 64 | 8.78 | 1,790 | — |
| 128 | 15.35 | 3,111 | — |
| 256 | 26.70 | 5,361 | — |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 42.5 s | 0.33 | 71.4 | 3.01 s | 0.33 answers/s |
| 8 | 46.8 s | 1.54 | 333.0 | 4.72 s | 1.70 answers/s |
| 16 | 49.0 s | 2.53 | 552.3 | 5.59 s | 2.86 answers/s |
| 32 | 50.0 s | 4.26 | 885.5 | 6.58 s | 4.86 answers/s |
| 64 | 51.0 s | 6.88 | 1402.9 | 8.03 s | 7.97 answers/s |
| 128 | 53.3 s | 11.53 | 2336.9 | 9.35 s | 13.69 answers/s |
| 256 | 55.4 s | 19.29 | 3872.9 | 10.89 s | 23.51 answers/s |

**Prompt mix at concurrency 32:** uniform 5.42 answers/s, 1,079.5 tok/s, p50 5.52 s · mixed 1.93 answers/s, 842.2 tok/s, p50 17.25 s.

**Thinking off**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 1.77 | 63.9 | 2218.7 | 0.56 s | 0.68 s | 99 % · 99 % · 100 % · 100 % |
| 8 | 6.83 | 248.2 | 8533.8 | 1.14 s | 1.53 s | 100 % · 99 % · 100 % · 100 % |
| 16 | 10.12 | 371.2 | 12663.0 | 1.54 s | 2.09 s | 97 % · 100 % · 100 % · 100 % |
| 32 | 8.28 | 304.8 | 10350.6 | 2.22 s | 13.75 s | 68 % · 82 % · 90 % · 97 % |
| 64 | 8.93 | 324.3 | 11159.2 | 4.27 s | 19.37 s | 48 % · 97 % · 76 % · 94 % |
| 128 | 26.18 | 968.0 | 32744.4 | 4.23 s | 8.92 s | 100 % · 89 % · 92 % · 94 % |
| 256 | 46.27 | 1695.7 | 57873.6 | 5.45 s | 8.24 s | 96 % · 97 % · 95 % · 95 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 1 | 1.77 | 63.9 | — |
| 8 | 6.83 | 248.2 | — |
| 16 | 10.12 | 371.2 | — |
| 32 | 8.28 | 304.8 | — |
| 64 | 8.93 | 324.3 | — |
| 128 | 26.18 | 968.0 | — |
| 256 | 46.27 | 1,696 | — |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 1 | 41.5 s | 1.71 | 61.6 | 0.57 s | 1.75 answers/s |
| 8 | 41.5 s | 6.58 | 239.5 | 1.18 s | 6.78 answers/s |
| 16 | 41.4 s | 9.77 | 358.4 | 1.60 s | 10.00 answers/s |
| 32 | 41.2 s | 8.04 | 296.0 | 3.93 s | 8.14 answers/s |
| 64 | 42.2 s | 8.46 | 307.5 | 7.32 s | 8.74 answers/s |
| 128 | 42.4 s | 24.72 | 914.1 | 4.99 s | 25.63 answers/s |
| 256 | 42.4 s | 43.65 | 1599.6 | 5.67 s | 45.14 answers/s |

**Prompt mix at concurrency 32:** uniform 13.25 answers/s, 490.4 tok/s, p50 2.16 s · mixed 3.17 answers/s, 1,120.7 tok/s, p50 15.59 s.

## Above 256 clients

**Thinking on, 256–1024**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 26.98 | 5445.1 | 40323.7 | 9.63 s | 19.46 s | 100 % · 100 % · 100 % · 100 % |
| 384 | 36.48 | 7236.8 | 54398.9 | 10.56 s | 21.97 s | 100 % · 100 % · 100 % · 100 % |
| 512 | 42.85 | 8489.1 | 63894.2 | 12.11 s | 24.71 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 54.33 | 10965.5 | 81207.7 | 14.82 s | 30.15 s | 100 % · 100 % · 100 % · 100 % |
| 1024 | 62.77 | 12501.4 | 93669.4 | 17.68 s | 34.99 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 26.58 | 5,365 | 1.01× |
| 384 | 36.36 | 7,214 | — |
| 512 | 42.28 | 8,376 | 1.01× |
| 768 | 51.82 | 10,459 | 1.05× |
| 1024 | 57.92 | 11,535 | 1.08× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 55.3 s | 19.51 | 3938.6 | 10.86 s | 23.58 answers/s |
| 384 | 58.5 s | 24.95 | 4950.7 | 12.10 s | 31.74 answers/s |
| 512 | 59.6 s | 28.74 | 5693.3 | 13.77 s | 37.17 answers/s |
| 768 | 61.7 s | 35.21 | 7106.3 | 16.79 s | 45.74 answers/s |
| 1024 | 63.9 s | 39.31 | 7828.6 | 19.81 s | 51.69 answers/s |

**Thinking off, 256–1024**

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 256 | 46.15 | 1693.7 | 57719.8 | 5.53 s | 8.19 s | 99 % · 100 % · 100 % · 97 % |
| 384 | 49.95 | 1844.6 | 62483.9 | 7.63 s | 12.14 s | 98 % · 95 % · 98 % · 98 % |
| 512 | 57.92 | 2132.3 | 72453.2 | 9.19 s | 14.24 s | 100 % · 100 % · 100 % · 100 % |
| 768 | 58.20 | 2140.5 | 72795.3 | 13.45 s | 21.14 s | 95 % · 98 % · 98 % · 100 % |
| 1024 | 68.40 | 2509.9 | 85547.5 | 16.04 s | 26.55 s | 100 % · 100 % · 100 % · 100 % |

Over the real run time — concurrency ÷ median latency, [why](../../../../benchmark/README.md#the-window-overstates-slow-answers):

| Concurrent | answers/s | output tok/s | v1 over by |
|---|---|---|---|
| 256 | 46.15 | 1,694 | — |
| 384 | 49.95 | 1,845 | — |
| 512 | 55.71 | 2,051 | 1.04× |
| 768 | 57.10 | 2,100 | 1.02× |
| 1024 | 63.84 | 2,343 | 1.07× |

Over the wall-clock time, measured, and concurrency ÷ mean latency:

| Concurrent | Wall | Answers/s (wall) | Output tok/s (wall) | Mean latency | C / mean latency |
|---|---|---|---|---|---|
| 256 | 42.4 s | 43.54 | 1597.9 | 5.68 s | 45.07 answers/s |
| 384 | 42.4 s | 47.18 | 1742.2 | 7.86 s | 48.84 answers/s |
| 512 | 43.5 s | 53.31 | 1962.3 | 9.26 s | 55.32 answers/s |
| 768 | 43.5 s | 53.53 | 1968.7 | 13.53 s | 56.77 answers/s |
| 1024 | 45.6 s | 59.98 | 2200.9 | 16.02 s | 63.93 answers/s |

## Reading

**Four copies roughly double what TP=4 delivers under load, at half the latency.** Over the real
run time, thinking on:

| Concurrent | TP=4 | four copies | four copies ÷ TP=4 | p50, TP=4 → four copies |
|---|---|---|---|---|
| 256 | 3,869 tok/s | 5,365 | 1.39× | 13.6 → 9.6 s |
| 512 | 4,539 | 8,376 | 1.85× | 22.3 → 12.1 s |
| 768 | 4,892 | 10,459 | 2.14× | 30.9 → 14.8 s |
| 1024 | 5,956 | **11,535** | 1.94× | 34.8 → 17.7 s |

Read by mean latency the factor at 1,024 is the same (10,296 against 5,453), and the cards stay
at 100 % with the curve still rising. That is 2.6 times the August SGLang patchset's best
(4,438 at 1,024) and twice MiMo's 5,608 at the same load.

**The price is the single request:** 79 against 95 tok/s single stream and a flat 73 tok/s decode
instead of 92, because each request's attention runs on one card. **Without thinking** the
copies reach 46 answers/s at 256 and 64 at 1,024, against 30 with TP=4, but between 32 and 64
clients the rate falls to 8–9 answers/s with the cards at 48–97 %: short requests spread
unevenly over the copies at that load.
