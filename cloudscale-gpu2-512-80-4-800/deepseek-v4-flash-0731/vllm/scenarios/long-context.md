# Scenario: long context — DeepSeek-V4-Flash-0731, vLLM TP=4 + EP

**Setup:** [vLLM 0.33.0 TP=4 + EP, FP8](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-08, 00:11–00:13

Served at 262,144 tokens, like every November run; the checkpoint itself reads 1M, which the
[SGLang stack](../../sglang/scenarios/long-context.md) verified in August.

| Target | Prefill (TTFT) | Prefill throughput | GPU | Needles |
|---|---|---|---|---|
| 64,000 | 9.5 s | 6,727 tok/s | 100 % | **3 of 3** |
| 128,000 | 21.0 s | 6,108 tok/s | 95–96 % | **3 of 3** |
| 250,000 | 42.8 s | 5,844 tok/s | 95–97 % | **3 of 3** |

Every needle found; prefill 13 % slower at 250k than at 64k. Decode behind 64k: 89.0 tok/s.
The KV pool holds 1,557,249 tokens, 5.9 requests of full length.
