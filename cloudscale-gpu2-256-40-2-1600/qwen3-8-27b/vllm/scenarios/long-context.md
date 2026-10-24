# Scenario: long context — vLLM TP=2

Needle-in-a-haystack at four depths, up to 240,000 tokens.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `Qwen3.8-27B` BF16 ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-24

## Method

Protocol [`v1`](../../../../benchmark/README.md), `bench.py --scenario longctx`, run
four times with `--target-tokens` at 64,000 / 128,000 / 180,000 / 240,000. Filler is
calibrated against the server's own tokeniser — 20.00 tokens per sentence here — and
three codes are planted at 10 %, 50 % and 90 % of the prompt. **The middle needle is the
actual test**: a model that only attends to the edges returns the outer two and misses
it.

The first three depths match the ones
[DeepSeek was measured at](../../../deepseek-v4-flash-0731/sglang/scenarios/long-context.md)
so the prefill figures are directly comparable. The fourth exists because this window is
262,144 and nothing here had been taken that far.

Against the engine on `127.0.0.1:8001` directly, embedding model resident — see
[single stream](single-stream.md#method).

**One run per depth.** DeepSeek has two runs at 180,000, 4 % apart.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Depth | Prompt | Prefill (TTFT) | Prefill tok/s | Total | GPU | Needles |
|---|---|---|---|---|---|---|
| 64,000 | 0.45 MB | 12.5 s | 5131 | 13.1 s | 100 % · 100 % | **3 of 3** |
| 128,000 | 0.90 MB | 29.5 s | 4343 | 30.2 s | 97 % · 97 % | **3 of 3** |
| 180,000 | 1.26 MB | 42.8 s | 4207 | 43.5 s | 98 % · 98 % | **3 of 3** |
| 240,000 | 1.68 MB | 63.2 s | 3796 | 63.9 s | 98 % · 97 % | **3 of 3** |

## Reading

**All three needles at every depth, including 240,000 tokens.** The middle needle came
back each time. That is the deepest verified retrieval in this repository — DeepSeek was
taken to 180,000 and also returned 3 of 3, and nothing else here was tested above that.

**Prefill degrades gently and predictably**: 5131 → 3796 tok/s across a 3.75× increase
in depth, a loss of 26 %. The curve is flattest between 128k and 180k (4343 → 4207, −3 %)
and steepest in the first step (64k → 128k, −15 %).

**A full-window request costs about a minute of prefill before the first token.** At
240,000 tokens the TTFT is 63.2 s and generation adds 0.7 s. Any client in front of this
needs its timeout set from the prefill, not from the answer — and the gateway's HAProxy
`timeout server` has already caused a
[504 on this machine](../../../README.md) for a far shorter request.

**Generation after a long prefill is almost free here**, 0.6–0.7 s for up to 600 tokens
at every depth. The cost of long context in this setup is entirely in prefill.

## Against DeepSeek-V4-Flash-0731

| Depth | Qwen prefill tok/s | DeepSeek prefill tok/s | ratio |
|---|---|---|---|
| 64,000 | 5131 | **8227** | 0.62 |
| 128,000 | 4343 | **7480** | 0.58 |
| 180,000 | 4207 | **7133** | 0.59 |
| 240,000 | 3796 | not measured | — |

**A steady 0.6× across the range**, the same ratio as
[single-stream decode](single-stream.md#against-deepseek-v4-flash-0731). Prefill is
compute-bound rather than bandwidth-bound, so the consistency across two different
bottlenecks is worth noting: on this hardware the dense 27 B model is about 60 % of the
284 B sparse one in both phases.

**Both recover 3 of 3 wherever they were both tested**, so depth capability does not
separate them — only speed does, and only above the depth DeepSeek was taken to does
Qwen have the field to itself.
