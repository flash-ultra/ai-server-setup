# Scenario: single stream — SGLang TP=2

One request at a time, no competing load.

**Setup:** [SGLang TP=2](../README.md) · `DeepSeek-V4-Flash-0731` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30, repeated 2026-09-22

## Method

Protocol `v1`, `--scenario single`, no deviations. **Thinking was off** — the default of
this setup, not a choice, see [reasoning cost](reasoning-cost.md). FP8 KV cache without
scaling factors, the only admissible setting.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Run 1 | Run 2 | Spread |
|---|---|---|---|
| Output | 75.3 tok/s | 75.5 tok/s | **0.3 %** |
| Total (incl. reasoning) | 2655.1 tok/s | 2594.6 tok/s | 2.3 % |
| Requests | 2.12 req/s | 2.08 req/s | 1.9 % |
| Latency p50 | 0.47 s | 0.47 s | 0 % |
| Tokens per answer | 35 (0 % reasoning) | 36 (0 % reasoning) | — |
| GPU utilisation | 95 % · 90 % | 93 % · 87 % | — |

Run 2 was measured on 2026-09-22 against a freshly started server on the same
configuration, 23 days after run 1.

## Reading

**0.47 s median for a complete answer** is the number that matters for interactive use.
[MiniMax-M2.5](../../../minimax-m2-5/vllm/scenarios/single-stream.md) needs 1.96 s on the
same cards, and 79 % of its budget goes into thinking it cannot switch off.

**35 tokens per answer, against MiniMax's 258.** The pinned prompt asks for a
three-sentence summary; 0731 obliges tersely. Every answers-per-second figure in this
directory is inflated by that relative to a model that writes longer — which is why the
[model README](../../README.md) puts the two side by side at equal thinking state instead
of comparing peaks.

**Output 75.3 tok/s against a total of 2655.1** is prompt throughput, not reasoning. At
2.12 requests per second with a ~1216-token prompt, prefill dominates the total column.
The total column is also the only one that moved between runs — 2.3 % against 0.3 % on
output — which fits prefill being the variable part.
The 0 % reasoning share is real here and verified against the `reasoning_effort=low` rows
in [reasoning cost](reasoning-cost.md).

## Not measured

- **Decode rate with prefill excluded.** `v1` does not produce it.
