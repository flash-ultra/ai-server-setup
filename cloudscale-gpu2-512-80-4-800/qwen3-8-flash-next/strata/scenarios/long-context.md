# Scenario: long context — Strata IQ3_S, four cards

Needle-in-a-haystack at 64k, 128k and 250k of the 262,144 window.

**Setup:** [Strata 0.2.11, IQ3_S, four cards](../README.md) ·
[the four-card machine](../../../README.md) · measured 2026-11-06, 12:08

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md),
`bench.py --scenario longctx --target-tokens 64000 / 128000 / 250000`, filler calibrated
against the server's tokeniser, needles at 10 / 50 / 90 %, thinking on, one streaming request
per size on an idle engine, `--prefill auto`.

## Result

The Q8_0 pack under the same engine: 4.4 / 7.5 / 14.1 s TTFT, **14,536 / 17,050 / 17,757 tok/s**,
3 of 3 needles at every size, cards at 31–81 %. IQ3_S:

<!-- protocol v1 · counted via usage fields -->

| Target | Prefill (TTFT) | Prefill throughput | Total | GPU | Needles |
|---|---|---|---|---|---|
| 64,000 | 3.8 s | **16,967 tok/s** | 4.4 s | 44 · 42 · 51 · 50 % | **3 of 3** |
| 128,000 | 6.2 s | **20,639 tok/s** | 6.9 s | 58 · 69 · 72 · 57 % | **3 of 3** |
| 250,000 | 11.4 s | **21,873 tok/s** | 11.9 s | 75 · 74 · 68 · 83 % | **3 of 3** |

**The fastest prefill in either repository, by a factor of 1.9 over the previous best
(the DeepSeek EXL3 pack on two of these cards, 11,386 tok/s) and 2.8 over vLLM FP8 on
these four** (7,840 at 250k). A full 250,000-token prompt is read in 11.4 s, and the rate
still rises with length: the pipeline is not full at 250k. Decode behind 64k:
[243 tok/s](single-stream.md), 8 % above the short-prompt rate rather than below it.

| Prefill tok/s | 64k | 128k | 250k |
|---|---|---|---|
| **Strata IQ3_S, 4× RTX PRO 6000** | **16,967** | **20,639** | **21,873** |
| Strata Q8_0, same cards | 14,536 | 17,050 | 17,757 |
| vLLM FP8 TP=4, same cards | 7,591 | 7,782 | 7,840 |
| Strata IQ3_S, Rocky 2× RTX PRO 4500 | 5,957 | 6,348 (120k) | — |
