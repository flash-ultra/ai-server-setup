# Scenario: single stream — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 23:49–23:51, decode 2026-11-08, 00:11

Protocol [`v1`](../../../../benchmark/README.md), both arms, without speculative decoding.
From this run on `bench.py` also reports the rate over the wall-clock time
([why](../../../../benchmark/README.md#the-window-overstates-slow-answers)).

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking on (server default) | `thinking: false` |
|---|---|---|
| Output | **95.3 tok/s** | 80.7 tok/s |
| Over the wall-clock time | 90.1 tok/s | 80.2 tok/s |
| Requests | 0.38 req/s | 2.23 req/s |
| Latency p50 | 2.59 s | 0.44 s |
| Tokens per answer | 254 (84 % reasoning) | 36 |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 114 / 148 | 0.05 / 0.04 s | **91.8 / 91.8 tok/s** |
| thinking off, run 1 / 2 | 122 / 116 | 0.04 / 0.04 s | **91.8 / 91.8 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.22 / 0.04 s | **90.6 / 90.3 tok/s** |
| behind a 64k prompt | 512 | 9.37 s | **89.0 tok/s** |

**92 tok/s, and a 64k prompt costs 3 % of it** — the flattest decode of the November runs, which
is what the compressed attention of V4 promises. The stock image gets there without the
draft module; [DSpark](dspark.md) is measured separately.
