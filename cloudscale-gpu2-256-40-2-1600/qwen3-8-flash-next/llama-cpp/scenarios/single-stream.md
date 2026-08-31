# Scenario: single stream — llama.cpp master

One request at a time, no competing load.

**Setup:** [llama.cpp `-sm layer`](../README.md) · `Qwen3.8-Flash-Next` UD-Q5_K_XL ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-31

## Method

Protocol `v1`, `--scenario single`, no deviations.

**`max_tokens` is pinned at 512, and this model does not always finish inside it.** On a
separate image question, budgets of 300 and 2500 both returned empty `content` with the
budget spent; 8000 produced the answer. Part of what this table counts is therefore
truncated thinking, not a finished reply.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Output | 88.5 tok/s |
| Total (incl. reasoning) | 656.8 tok/s |
| Requests | 0.45 req/s |
| Latency p50 | 2.22 s |
| Tokens per answer | 197 (0 % reasoning) |
| GPU utilisation | 46 % · 45 % |

## Reading

**2.22 s for a complete answer is the case this model is good at.** It is the interactive
single-user number, and it is the only column where this setup is competitive:
[DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/single-stream.md) is at
0.47 s but answers in 35 tokens; this one writes 197.

**46 % on both cards, with a single request in flight.** Nothing else is running. That is
`-sm layer` alternating between the cards, and it is the same number the
[concurrency ladder](concurrent-load.md) shows at every level.

**0 % reasoning is "not reported".** llama.cpp omits the field. 197 tokens for a
three-sentence summary is not a model that skipped thinking.

## Not measured

- **Decode rate with prefill excluded.**
- **Variance.** One run.
