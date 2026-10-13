# Scenario: single stream — vLLM, MiMo build

One request at a time, no competing load.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13, twice

## Method

Protocol `v1`, `--scenario single`, no deviations. Thinking is **on** — the default of
this checkpoint. It can be switched off, and the key was
[verified](../README.md#thinking-can-be-switched-off-and-only-two-of-five-ways-work)
rather than assumed; [reasoning cost](reasoning-cost.md) covers that arm.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Run 1 | Run 2 | Spread |
|---|---|---|---|
| Output | 113.9 tok/s | 114.7 tok/s | **0.7 %** |
| Total (incl. reasoning) | 2184.5 tok/s | 2215.8 tok/s | 1.4 % |
| Requests | 1.70 req/s | 1.73 req/s | 1.8 % |
| Latency p50 | 0.57 s | 0.56 s | 1.8 % |
| Tokens per answer | 67 (20 % reasoning) | 67 (21 % reasoning) | — |
| GPU utilisation | 99 % · 100 % | 99 % · 100 % | — |

An earlier series on the same setup at a 49,152 window measured 114.7 and 114.4 tok/s.
**Quadrupling the served window changed single-stream throughput by 0.3 %** — see
[the window finding](../README.md#a-token-gets-cheaper-as-the-window-grows).

## Reading

**114.3 output tok/s against 75.4 for the production model, and it is thinking while it
does it.** On the same cards,
[DeepSeek-V4-Flash-0731 under SGLang](../../../deepseek-v4-flash-0731/sglang/scenarios/single-stream.md)
delivers 75.3–75.5 tok/s with thinking off and 35 tokens per answer. DeepSeek has no
thinking-on single-stream arm — the only thinking-on figures for it are at
[concurrency 8 and 32](../../../deepseek-v4-flash-0731/sglang/scenarios/reasoning-cost.md),
where thinking costs it a factor of 4 in answers per second. Here it costs 0.6 s per
answer in total.

**99 % on both cards with a single request in flight.** That is the signature of working
tensor parallelism: DeepSeek measures 95 % · 90 % and 93 % · 87 % here, llama.cpp sits in
the forties. MiniMax-M2.5 also reaches 100 % · 100 % at concurrency 1 — at 0.42 answers/s
against 1.70 here, which is the reminder that utilisation is not throughput.

**The reasoning share is reported, and it is modest.** 20–21 % of 67 tokens, against 85 % of
290 for DeepSeek with thinking on. The field is populated at all only because
`--reasoning-parser mimo` is configured; without it the thinking block is not separated
out and the split cannot be read.

## Not measured

- **Decode rate with prefill excluded.** `v1` does not produce it.
- **A cold second run.** Both runs went against the same server process.
