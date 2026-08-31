# Scenario: single stream — vLLM 0.28.0

One request at a time, no competing load. The interactive single-user case.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `nvidia/MiniMax-M2.5-NVFP4` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30

## Method

Protocol `v1`, `--scenario single`, no deviations. `max_tokens` 512, 40 s window, 3
warmup requests discarded, counted via `usage`. The pinned prompt asks for a
three-sentence summary of ~1216 tokens of filler.

Both cards were otherwise idle; no second model was resident.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Output | 122.4 tok/s |
| Total (incl. reasoning) | 715.7 tok/s |
| Requests | 0.47 req/s |
| Latency p50 | 1.96 s |
| Tokens per answer | 258 (79 % reasoning) |
| GPU utilisation | 100 % · 100 % |

## Where the tokens go

```
258 tokens per answer

reasoning  204  ████████████████████████████████████████░░░░░░░░░░  79 %
visible     54  ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  21 %
```

The visible share is what a client sees; the whole bar is what it pays for.

## Reading

**The 79 % reasoning share is the number that matters for budgeting.** An answer of 258
tokens carries roughly 54 tokens of visible text. A client that sets `max_tokens` to a
value tuned for visible output will get an empty `content` back — the budget goes into
thinking first. Observed directly: at `max_tokens` 64 the response returned
`content: ""` with a `stop` finish reason.

**Both cards at 100 % on a single request** is the tensor-parallel signature. The same
machine under llama.cpp with `-sm layer` leaves one card idle half the time, because
`-sm row` [does not load here](../../../README.md#llamacpp-cannot-split-across-these-cards).

**122.4 tok/s is request-shaped, not a decode rate.** Prefill of the ~1216-token prompt
sits inside the 1.96 s. The separate decode rate was not measured with a streaming tool,
so there is no equivalent of the kit-style TTFT/decode split available on the
[older machine's NVFP4 run](../../../../cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/vllm-b12x/scenarios/single-stream.md).

## Not measured

- **Decode rate with prefill excluded.** Needs a streaming client; `v1` does not produce it.
- **Variance.** One run.
