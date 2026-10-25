# Scenario: reasoning cost — vLLM + EXL3, TP=2

What thinking costs, measured at two concurrency levels with the switch verified first.

**Setup:** [vLLM + EXL3 plugin, TP=2](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3
3 bpw · [cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-25

## Method

Protocol [`v1`](../../../../benchmark/README.md), `bench.py --scenario reasoning`, at
concurrency 8 and 32, against the engine on `127.0.0.1:8010`. Measurement configuration,
nothing else on the cards.

**The switch was probed before the run, not assumed.** Of five candidate keys, two work:
`chat_template_kwargs: {thinking: false}` and `chat_template_kwargs: {enable_thinking:
false}` take `reasoning_tokens` to 0, while the top-level `thinking` flag, `reasoning_effort:
"low"` and a numeric `reasoning_effort` do not — the
[probe table](../../README.md#model-specific-gotchas) has all five. The runs below use
`chat_template_kwargs: {thinking: false}`.

`reasoning_effort: low` is included as its own variant precisely because the probe said
it does nothing; the table shows what "does nothing" looks like at scale.

**One run per cell.**

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrency | Variant | Answers/s | Output tok/s | Tok/answer | Reasoning | Chars/answer | p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 1.62 | 258.4 | 159 | 75 % | 246 | 4.94 s | 84 % · 90 % |
| 8 | `reasoning_effort=low` | 1.65 | 244.3 | 148 | 72 % | 255 | 5.12 s | 85 % · 89 % |
| 8 | **thinking off** | **2.98** | 192.8 | 65 | **0 %** | **399** | **2.83 s** | 85 % · 88 % |
| 32 | default | 2.27 | 369.2 | 162 | 75 % | 254 | 20.17 s | 83 % · 87 % |
| 32 | `reasoning_effort=low` | 2.27 | 348.4 | 153 | 73 % | 251 | 19.76 s | 88 % · 91 % |
| 32 | **thinking off** | **3.55** | 221.2 | 62 | **0 %** | **383** | **11.12 s** | 81 % · 89 % |

## Reading

**Switching thinking off is worth 84 % more answers per second at concurrency 8** and
56 % at 32, at 43 % lower median latency. It costs 25 % of output tokens per second,
which is the usual direction: fewer tokens produced, more answers finished.

**The visible answer gets longer when thinking is switched off** — 399 characters
against 246, a 62 % increase, while total tokens per answer fall from 159 to 65. With
thinking on, three quarters of the generation is scratchpad and the reply itself is
*terser*. Anyone judging answer quality by reply length would read this backwards.

**`reasoning_effort=low` changes nothing measurable**, exactly as the probe predicted:
1.65 against 1.62 answers per second, 148 against 159 tokens, 72 % against 75 %
reasoning. Every difference is within the run-to-run variation of a single run. This is
what an accepted-but-ignored request option looks like in a results table — plausible,
small, and entirely noise.

**It is the reason the protocol requires probing the key.** Had only this variant been
run, the honest-looking conclusion would have been "reasoning effort has a mild effect
here", and the real switch — worth 84 % — would have been missed. The machine's
[general finding](../../../../README.md#switches-that-a-model-does-not-know-are-accepted-not-rejected)
now has a third model behind it.

**The gain is larger at low concurrency than at high.** 84 % at 8 slots against 56 % at
32 — with 8 engine slots, concurrency 32 is already queueing, and a queue absorbs part
of what shorter answers would otherwise buy.
