# Scenario: reasoning cost — vLLM TP=2

What thinking costs per answer, at two concurrency levels, three variants.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `Qwen3.8-27B` BF16 ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-24

## Method

Protocol [`v1`](../../../../benchmark/README.md), `bench.py --scenario reasoning
--thinking-key enable_thinking`. Three variants at concurrency 8 and 32: the default,
`reasoning_effort: "low"`, and thinking switched off.

**The key had to be named explicitly.** `bench.py` defaults to `thinking`, which is
DeepSeek's key and is
[silently ignored here](../README.md#thinking-is-on-by-default-and-two-of-four-switches-work) —
it returns a normal answer with thinking still on, and the row would have read "switching
thinking off changes nothing". Verified before the run: `enable_thinking: false` takes
`reasoning_tokens` from 93 to 0.

Against the engine on `127.0.0.1:8001` directly, embedding model resident.

**One run per cell.**

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields · thinking key: enable_thinking -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 1.70 | 329.5 | 194 | 78 % | 252 | 4.85 s | 100 % · 100 % |
| 8 | `reasoning_effort=low` | 2.08 | 312.6 | 151 | 68 % | 283 | 4.05 s | 100 % · 100 % |
| 8 | thinking off | **4.72** | 249.7 | 53 | 0 % | 334 | **1.68 s** | 100 % · 100 % |
| 32 | default | 4.85 | **942.9** | 194 | 77 % | 260 | 6.69 s | 100 % · 100 % |
| 32 | `reasoning_effort=low` | 5.60 | 857.5 | 153 | 69 % | 280 | 5.93 s | 100 % · 100 % |
| 32 | thinking off | **9.80** | 525.2 | 54 | 0 % | 337 | **3.22 s** | 100 % · 100 % |

## Reading

**Thinking costs a factor of 2.8 in answers per second** at concurrency 8 and 2.0 at 32,
and buys 3.7× the tokens per answer. The
[quality scenario](quality.md) measures what those tokens are worth: +13.5 points of
IFEval `prompt_strict`, and between +0.6 and +2.0 on everything else.

**`reasoning_effort` is a dial here, not a switch.** It reduces thinking rather than
removing it — 194 → 151 tokens per answer, 78 % → 68 % reasoning share — and buys 22 %
more answers per second. **On DeepSeek-0731 the same parameter does the opposite**: it
is the thing that turns thinking *on*, from a default of off. Same parameter name, same
machine, opposite effect, no error either way.

**The visible answer gets *longer* when thinking is switched off**, 252 → 334 characters
at concurrency 8. That is the clearest single argument for counting via `usage` rather
than the rendered text: by characters of visible output, the thinking-off arm looks like
it produced *more*, while producing 3.7× fewer tokens. A stream-delta count that misses
`reasoning` would report this arm as the more productive one.

**Both cards hold 100 % in all six rows**, including the thinking-off rows at
concurrency 8 where only 4.72 answers per second are coming out. Utilisation says
nothing about headroom on this setup.
