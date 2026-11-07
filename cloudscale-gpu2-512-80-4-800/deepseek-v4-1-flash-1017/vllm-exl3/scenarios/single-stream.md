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

**Decode, measured separately** (one streaming request; `decode.py` now sends the API key —
its first run here got 401s and was repeated after the eval)

| | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 146 / 127 | 0.19 / 0.16 s | **175.2 / 186.2 tok/s** |
| thinking off, run 1 / 2 | 33 / 74 | 0.16 / 0.15 s | **159.1 / 188.4 tok/s** |
| thinking on, 1,500 tokens forced, run 1 / 2 | 1500 / 1500 | 0.51 / 0.17 s | 216.5 / 308.5 tok/s |
| thinking on, behind a 64k prompt | 164 | 4.65 s | **168.9 tok/s** |

The forced 1,500-token rows run past the model's own end of answer (`min_tokens`), into text
the k=7 drafter predicts almost perfectly; they show the drafter's ceiling, not a real
answer's rate. The 160–190 tok/s of the natural answers is the figure to quote, against
114–128 on two cards.

**153 tok/s, the fastest DeepSeek single stream measured**: 1.12× the same pack on two
cards (136.5) and 1.37× Strata's 2.25-bit set on these four (111.8). TP=4 adds all-reduce
hops over PCIe, and here they run through NCCL rather than the pack's 8-bit kernels; the
speculative drafter (k=7) is what keeps the single stream ahead anyway.
