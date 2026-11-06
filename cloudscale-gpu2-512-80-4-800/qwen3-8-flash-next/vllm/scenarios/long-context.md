# Scenario: long context — vLLM TP=4

Needle-in-a-haystack at 64k, 128k and 250k of the 262,144-token window: prefill
throughput and whether the three codes come back.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md) · `Qwen3.8-Flash-Next-FP8` ·
[the four-card machine](../../../README.md) · measured 2026-11-06

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md),
`bench.py --scenario longctx --target-tokens 64000 / 128000 / 250000`. Filler calibrated
against the server's tokeniser (20.0 tokens per sentence), needles at 10 / 50 / 90 %,
thinking on, one streaming request per size on an idle engine. 250k is the largest
target under the 262,144 window with room for the answer.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Target | Prefill (TTFT) | Prefill throughput | Total | GPU | Needles |
|---|---|---|---|---|---|
| 64,000 | 8.4 s | **7591 tok/s** | 8.7 s | 100 % × 4 | **3 of 3** |
| 128,000 | 16.4 s | **7782 tok/s** | 16.7 s | 99 / 99 / 98 / 96 % | **3 of 3** |
| 250,000 | 31.9 s | **7840 tok/s** | 32.1 s | 93 % × 4 | **3 of 3** |

**Prefill does not slow down with length**: 7.6 → 7.8 k tok/s from 64k to 250k. That is
the sparse attention doing what it is for. A full-window prompt costs 32 s before the
first token. Decode behind 64k: [113 tok/s](single-stream.md), 2 % under the short-prompt rate.

Against Strata on the Rocky two-card machine (2× RTX PRO 4500) (same model, IQ3_S, two 32 GB cards): 5957 tok/s at 64k and
6348 at 120k, 3 of 3 at both, 131k window. This machine reads prompts 25 % faster and
twice as far.
