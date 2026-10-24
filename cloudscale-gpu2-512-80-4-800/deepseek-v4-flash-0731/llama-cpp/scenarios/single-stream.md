# Scenario: single stream — llama.cpp

One request at a time, no competing load. This is the case llama.cpp is good at.

**Setup:** [llama.cpp layer-split](../README.md) · DeepSeek-V4-Flash-0731 UD-Q8_K_XL ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-14

## Method

Prompt ~1000 tokens at empty context, `max_tokens` 200, concurrency 1. Generation
figures with and without `--spec-type draft-dspark` on otherwise identical
configuration.

## Results

| Metric | Value |
|---|---|
| Generation with DSpark | **91 tok/s** |
| Generation without DSpark | 54.9 tok/s |
| Draft acceptance | 64–69 % |
| Prompt processing (empty context) | 2638 tok/s |
| Output under the load test at C=1 | 85.0 tok/s · 0.42 req/s |
| TTFT p50 | 0.05 s |
| GPU utilisation | 21 · 21 · 22 · 25 % |

## Reading

**Speculative decoding is the single largest win here.** 91 against 54.9 tok/s is a
66 % gain from one flag, and it costs only the second GGUF for the draft model. Nothing
else in this setup moved the number that far.

**TTFT is the best of both stacks.** 0.05 s against
[0.15 s for SGLang](../../sglang/scenarios/single-stream.md) — no 46 GB image, no graph
capture, 20 s startup. For a single user at short context this setup feels faster than
the production stack.

**The cards are already idle at concurrency 1.** 21–25 % per card, and that does not
change under load — see [concurrent-load.md](concurrent-load.md). The layer-split
ceiling is present from the first request; it just is not painful yet.

**Watch the reasoning share when planning.** 96 % of generated tokens are reasoning
tokens, so a visible answer of 10 tokens can cost 250 tokens of generation. At 91 tok/s
that is under three seconds, but it scales linearly with everything else.
