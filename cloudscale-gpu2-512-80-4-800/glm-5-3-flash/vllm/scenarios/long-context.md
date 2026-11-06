# Scenario: long context — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4 EP, NVFP4](../README.md) · `GLM-5.3-Flash` · [the four-card machine](../../../README.md) · measured 2026-11-06, 18:35–18:37

## Method

Protocol [`v1`](../../../../benchmark/README.md), `--scenario longctx --target-tokens 64000 / 128000 / 250000`,
needles at 10 / 50 / 90 %, default thinking, one request per size on an idle engine.

## Result

<!-- protocol v1 · counted via usage fields -->

| Target | Prefill (TTFT) | Prefill throughput | Total | GPU | Needles |
|---|---|---|---|---|---|
| 64,000 | 10.1 s | **6,353 tok/s** | 10.4 s | 100 % × 4 | **3 of 3** |
| 128,000 | 24.1 s | **5,301 tok/s** | 24.4 s | 87–91 % | **3 of 3** |
| 250,000 | 39.3 s | **6,360 tok/s** | 39.5 s | 96–99 % | **3 of 3** |

**Flat from 64k to 250k** (the 128k dip is a single run with the cards below 91 %), where
MiMo, with nine full-attention layers, falls from 6.1 k to 3.6 k. Decode behind 64k:
100.4 tok/s, 1 % under the short-prompt rate.

| Prefill tok/s on the four-card machine | 64k | 128k | 250k |
|---|---|---|---|
| Qwen3.8-Flash-Next IQ3_S · Strata | 16,967 | 20,639 | 21,873 |
| Qwen3.8-Flash-Next FP8 · vLLM | 7,591 | 7,782 | 7,840 |
| **GLM-5.3-Flash NVFP4 · vLLM** | 6,353 | 5,301 | 6,360 |
| MiMo-V2.6-Flash-RL FP8 · vLLM | 6,104 | 4,865 | 3,561 |
