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

## Full context

The stock image does not start with `--max-model-len 1048576`: FlashInfer's SM120 sparse-MLA
decode stops graph capture with the same `attention workspace insufficient for resolved plan` as
the [four copies](data-parallel.md). With the same one-line change — the fixed 128 MiB workspace
at 1 GiB — it starts in 492 s and reads a million-token window. Measured 2026-11-08, 15:26–15:33,
TP=4 + EP, everything else as above.

| Target | Prefill (TTFT) | Prefill throughput | Needles |
|---|---|---|---|
| 250,000 | 43.6 s | 5,729 tok/s | **3 of 3** |
| 500,000 | 102.6 s | 4,875 tok/s | **3 of 3** |
| 960,000 | 257.8 s | 3,724 tok/s | **3 of 3** |

**Every needle found at 960k**, in 4 min 18 s; the August SGLang patchset took 471 s for a full
million, the [DeepSeek-V4.1 EXL3 pack](../../../deepseek-v4-1-flash-1017/vllm-exl3/scenarios/long-context.md)
reads 960k in 88 s. The server reports 4,285,074 cache tokens at this window size, against
1,557,249 at 262,144.

