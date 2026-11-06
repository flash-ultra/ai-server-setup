# Scenario: single stream — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4 EP, NVFP4](../README.md) · `GLM-5.3-Flash` · [the four-card machine](../../../README.md) · measured 2026-11-06, 18:18–18:19 and 18:35

## Method

Protocol [`v1`](../../../../benchmark/README.md), **default arm only**: thinking cannot be
switched off ([why](../README.md#pinned-values)). Decode via `decode.py`, one streaming
request per row.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking on (default, effort max) |
|---|---|
| Output | **103.5 tok/s** |
| Total, incl. prompt | 439.8 tok/s |
| Requests | 0.28 req/s |
| Latency p50 | 3.49 s |
| Tokens per answer | 376 (**83 %** reasoning) |
| GPU utilisation | 99 % on all four |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| default, run 1 / 2 | 326 / 394 | 0.25 / 0.24 s | **101.9 / 101.9 tok/s** |
| `enable_thinking: false` (ignored), run 1 / 2 | 396 / 381 | 0.24 / 0.24 s | **101.9 / 102.0 tok/s** |
| 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.31 / 0.23 s | **101.1 / 101.2 tok/s** |
| behind a 64k prompt | 375 | 10.72 s | **100.4 tok/s** |

**Decode is a flat 101–102 tok/s whatever the length or the context**, 1 % slower behind
64k. Against MiMo (143) and Qwen (115) on the same cards, GLM is the slowest decoder and,
at 376 tokens per answer, by far the longest thinker.
