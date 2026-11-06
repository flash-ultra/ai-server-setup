# Scenario: single stream — Strata IQ3_S, four cards

One request at a time, both thinking arms, plus the decode rate measured apart from prefill.

**Setup:** [Strata 0.2.11, IQ3_S, layer split over four cards, 8 slots](../README.md) ·
[the four-card machine](../../../README.md) · measured 2026-11-06, 12:04–12:08

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md), no
deviations, `strata-bench.sh`
against `127.0.0.1:8080`. Thinking switch verified first: `enable_thinking: false` and
`reasoning_effort: "none"` both take the answer from 50 to 4 completion tokens. Strata's `usage`
has no `reasoning_tokens`, so the reasoning share below reads 0 % in both arms; the 210 tokens
of the thinking-on answer are 79 % thinking by the vLLM measurement of the same prompt. The
1,500-token decode rows are shorter than labelled: Strata honours neither `min_tokens` nor
`ignore_eos`, the same as on the Rocky two-card machine (2× RTX PRO 4500).

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **225.3 tok/s** | 140.2 tok/s |
| Total, incl. prompt | 1583.0 tok/s | 3534.1 tok/s |
| Requests | 1.07 req/s | **2.77 req/s** |
| Latency p50 | 0.90 s | **0.35 s** |
| Tokens per answer | 210 | 51 |
| GPU utilisation | **21 · 20 · 21 · 34 %** | 16 · 14 · 15 · 25 % |

**Decode, measured separately**

| | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 164 / 198 | 0.14 / 0.08 s | **224.4 / 253.7 tok/s** |
| thinking off, run 1 / 2 | 48 / 53 | 0.09 / 0.05 s | **224.5 / 222.1 tok/s** |
| thinking on, "1,500 tokens" (300 / 191 generated) | 300 / 191 | 0.06 / 0.05 s | **238.1 / 238.8 tok/s** |
| thinking on, behind a 64k prompt | 164 | 3.70 s | **243.0 tok/s** |

## The Q8_0 pack, same engine

unsloth's Q8_0 (188 GB, 119.5 GiB of experts loaded at 18.7 GiB/s in 70 s, 100 % resident,
45–47 GB of VRAM per card), `--parallel 8`, measured 13:49–13:52:

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** | thinking **off** |
|---|---|---|
| Output | **187.2 tok/s** | 125.7 tok/s |
| Requests | 0.90 req/s | 2.52 req/s |
| Latency p50 | 1.11 s | 0.39 s |
| Tokens per answer | 208 | 50 |
| GPU utilisation | 22 · 21 · 21 · 33 % | 18 · 16 · 15 · 23 % |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 338 / 246 | 0.14 / 0.08 s | **167.7 / 173.8 tok/s** |
| thinking off, run 1 / 2 | 49 / 45 | 0.10 / 0.06 s | **183.7 / 197.1 tok/s** |
| thinking on, "1,500 tokens" (165 / 159 generated) | 165 / 159 | 0.06 / 0.05 s | **222.0 / 214.3 tok/s** |
| thinking on, behind a 64k prompt | 214 | 4.31 s | **187.8 tok/s** |

**Eight bits cost 17 % of the single stream against the 3-bit pack (187 against 225) and
still beat vLLM's FP8 with its draft (175).** Same utilisation, same shape: the engine's
pipeline, not the weight bytes, is the limit on this machine.

## Against the other setups of this model

| Output tok/s, single stream | thinking on | thinking off | decode |
|---|---|---|---|
| **Strata IQ3_S, 4× RTX PRO 6000** (this) | **225.3** | **140.2** | **222–254** |
| Strata Q8_0, same cards | 187.2 | 125.7 | 168–222 |
| vLLM FP8 TP=4 + MTP draft, same cards | 175.4 | 132.4 | 163–192 |
| vLLM FP8 TP=4, no draft, same cards | 110.4 | 97.9 | 115 |
| Strata IQ3_S, 2× RTX PRO 4500 (Rocky 2× RTX PRO 4500) | 141.4 | 108.5 | 136–150 |

**The fastest single stream measured in either repository, at a fifth of the cards'
capacity.** 225 tok/s with the four cards at 20–34 %: the engine, not the hardware, sets
this number. Against the two-card Rocky machine the same pack gains 1.6× from cards that
are several times faster, which says the same thing. vLLM with its own MTP draft is 22 %
behind on the identical checkpoint family; without the draft it is half.
