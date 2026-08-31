# Scenario: reasoning cost — SGLang TP=2

What thinking costs per answer, and which switch actually moves it.

**Setup:** [SGLang TP=2](../README.md) · `DeepSeek-V4-Flash-0731` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30

## Method

Protocol `v1`, `--scenario reasoning`, no deviations. Three variants at concurrency 8 and
32: the setup's default, `reasoning_effort=low`, and thinking disabled through
`chat_template_kwargs: {thinking: false}` — the key the protocol names for DeepSeek-V4.

**The key was verified before the run**, as the protocol requires: through a gateway with
`--reasoning-parser deepseek-v4`, a plain request reports 84 reasoning tokens and 235
characters of `reasoning_content`; with `thinking: false` both go to zero. The key is
real, not silently ignored.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 6.22 | 228.2 | 37 | 0 % | 224 | 1.28 s | 95 % · 75 % |
| 8 | `reasoning_effort=low` | 1.57 | 457.5 | 290 | 85 % | 274 | 5.30 s | 100 % · 97 % |
| 8 | thinking off (`thinking`) | 6.28 | 228.0 | 36 | 0 % | 222 | 1.26 s | 94 % · 76 % |
| 32 | default | 11.90 | 431.2 | 36 | 0 % | 221 | 2.71 s | 94 % · 80 % |
| 32 | `reasoning_effort=low` | 3.65 | 1017.0 | 279 | 85 % | 262 | 9.37 s | 98 % · 93 % |
| 32 | thinking off (`thinking`) | 11.88 | 430.0 | 36 | 0 % | 221 | 2.75 s | 91 % · 79 % |

## Reading

**The default is thinking off.** `default` and `thinking off` are the same measurement —
6.22 against 6.28, 37 against 36 tokens, 0 % both. The key works, it just has nothing to
switch off. **Every other number in this directory was therefore measured without
thinking**, and that has to travel with them.

**`reasoning_effort=low` is what turns thinking on**, and it costs a factor of 4 in
answers per second: 6.22 → 1.57 at concurrency 8, 11.90 → 3.65 at 32. Tokens per answer go
from 36 to 290, of which 85 % is reasoning.

**Visible output barely changes.** 222 against 274 characters per answer — thinking adds
eight times the tokens and roughly a fifth more visible text. Whether that fifth is worth
four times the throughput is a quality question this scenario cannot answer.

**Output tokens per second go up while answers go down.** 228 → 457 at concurrency 8. The
machine is busier and delivers more tokens; the user waits longer for each answer. Which
column matters depends on whether you are paying for tokens or waiting for a reply.

**This is the scenario that makes the cross-model comparison honest.** MiniMax-M2.5 on the
same cards [cannot switch thinking off](../../../minimax-m2-5/README.md#model-specific-gotchas)
— no key moves it. Comparing its 4.25 answers/s at concurrency 32 against 11.90 here
compares a thinking model with a non-thinking one. Against the `reasoning_effort=low` row,
3.65, MiniMax is ahead.

## Not measured

- **`reasoning_effort` above `low`.** The protocol pins `low`; higher settings were not tried.
- **Quality difference.** The whole point of thinking, and not measurable here.
- **Concurrency other than 8 and 32.**
