# Scenario: single stream — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4](../README.md) · `MiMo-V2.6-Flash-RL` · [the four-card machine](../../../README.md) · measured 2026-11-06, 16:56–16:58 and 17:16

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations, against `127.0.0.1:8000`.
Thinking switch verified first (11 → 0 reasoning tokens). One run per arm; the two-card
series measured two runs 0.7 % apart. Decode is `decode.py`: one streaming request, tokens
after the first divided by duration minus TTFT.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **140.2 tok/s** | 137.3 tok/s |
| Total, incl. prompt | 2637.1 tok/s | 3675.3 tok/s |
| Requests | 2.05 req/s | **2.90 req/s** |
| Latency p50 | 0.48 s | **0.34 s** |
| Tokens per answer | 68 (21 % reasoning) | 47 (0 %) |
| GPU utilisation | 98 % on all four | 97–98 % |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 50 / 47 | 0.05 / 0.03 s | **147.3 / 147.5 tok/s** |
| thinking off, run 1 / 2 | 44 / 34 | 0.03 / 0.02 s | **143.3 / 143.1 tok/s** |
| thinking on, 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.24 / 0.04 s | **143.3 / 143.5 tok/s** |
| thinking on, behind a 64k prompt | 53 | 10.99 s | **132.8 tok/s** |

**143 tok/s decode, 1.21× the two cards' 118.5.** The thinking arms barely differ because
the model thinks for 14 tokens on this prompt. Against the other models on this machine,
single stream with thinking on: Strata Qwen3.8-Flash-Next IQ3_S 225, vLLM Qwen FP8 with
its MTP draft 175, this 140, vLLM Qwen FP8 without draft 110.
