# Scenario: single stream — Hy3, TP=4

**Setup:** [vLLM 0.33.0 TP=4, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 23:28–23:30 (repeat) and 21:01 (decode)

Protocol [`v1`](../../../../benchmark/README.md), both arms. The first run at 20:42 shared its
window with two probe requests; this is the repeat, and it gave the same figures.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | `reasoning_effort: high` (server default) | `no_think` |
|---|---|---|
| Output | **89.6 tok/s** | 81.8 tok/s |
| Over the real run time | 84.5 tok/s | 79.1 tok/s |
| Requests | 0.17 req/s | 1.45 req/s |
| Latency p50 | 6.02 s | 0.67 s |
| Tokens per answer | 512, the cap | 56 |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| `high`, run 1 / 2 | 512 / 512 | 0.34 / 0.04 s | **85.5 / 85.5 tok/s** |
| `no_think`, run 1 / 2 | 512 / 512 | 0.04 / 0.04 s | **85.4 / 85.3 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.04 / 0.04 s | **85.2 / 85.3 tok/s** |
| behind a 64k prompt | 512 | 19.52 s | **74.9 tok/s** |

**85 tok/s, flat to 1,500 tokens**, without the MTP head the card recommends. Behind a 64k
prompt decode loses 12 %. At `high` the protocol answer always reaches the 512-token cap. The
engine reports no reasoning tokens for this parser, although the thinking text arrives in its
own field ([pinned values](../README.md#pinned-values)), so the protocol's reasoning share
reads 0 % in both arms.
