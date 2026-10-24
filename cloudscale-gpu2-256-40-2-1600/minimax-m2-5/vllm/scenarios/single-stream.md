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

## Decode rate, measured separately

`v1` reports output tokens over a 40 s window, which folds one prefill into every
answer. A streaming request separates the two: completion tokens after the first,
divided by `duration − TTFT`, counted from `usage`. Measured 2026-10-24 against the
engine directly, this model alone on both cards, 1500 completion tokens per run.

| | tokens | TTFT | Decode |
|---|---|---|---|
| run 1 | 1500 | 0.09 s | **116.6 tok/s** |
| run 2 | 1500 | 0.02 s | **116.7 tok/s** |

**116.6 tok/s over 1500 tokens — and the `v1` column above reads *higher*, at 122.4.**
That ordering looks impossible, because window throughput also carries prefill and
should therefore sit below the decode rate. The explanation is in this page's own
numbers: 258 tokens at a p50 of 1.96 s is about 132 tok/s, so at a short generation this
setup decodes faster than it does at 1500.

**Decode slows as the KV cache grows within one request** — roughly 12 % between a
258-token answer and a 1500-token one here. A decode rate therefore needs its generation
length stated, exactly as a throughput figure needs its concurrency. The 1500-token
figure is the one comparable across the models on this machine; it is not the figure
that applies to a short chat turn.

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
