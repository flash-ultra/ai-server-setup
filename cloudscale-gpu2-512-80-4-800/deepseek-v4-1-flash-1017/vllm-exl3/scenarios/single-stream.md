# Scenario: single stream — EXL3 on four cards

**Setup:** [pack recipe, `PROFILE=8x REPLICA=0`, NCCL all-reduce](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3 3 bpw · [the four-card machine](../../../README.md) · measured 2026-11-07

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations; the bench client sends the
pack's required API key from `BENCH_API_KEY`. Thinking switch verified (19 → 0 reasoning tokens).

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **153.2 tok/s** | 116.4 tok/s |
| Total, incl. prompt | 1269.2 tok/s | 2665.8 tok/s |
| Requests | 0.90 req/s | 2.10 req/s |
| Latency p50 | 1.11 s | 0.49 s |
| Tokens per answer | 170 (76 % reasoning) | 55 (0 %) |
| GPU utilisation | 93–98 % | 89–96 % |

**153 tok/s, the fastest DeepSeek single stream measured**: 1.12× the same pack on two
cards (136.5) and 1.37× Strata's 2.25-bit set on these four (111.8). TP=4 adds all-reduce
hops over PCIe, and here they run through NCCL rather than the pack's 8-bit kernels; the
speculative drafter (k=7) is what keeps the single stream ahead anyway.
