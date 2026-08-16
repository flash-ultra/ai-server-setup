# Scenario: reasoning cost — llama.cpp

Which control actually shortens the trace on this checkpoint — and which one is inert.

**Setup:** [llama.cpp single-card](../README.md) · Muse-Glimmer-30B BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1`, concurrency 8 and 32, three variants per level. The thinking-off row uses
the protocol default key `thinking`, deliberately: this checkpoint's chat template
contains no thinking switch at all — neither `thinking` nor `enable_thinking` appears in
it — and the row is kept to show what an inert switch looks like in a table.

## Measurements

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Chars/answer | Latency p50 | GPU |
|---|---|---|---|---|---|---|---|
| 8 | default | 0.20 | 78.2 | 391 | 297 | 64.30 s | 96 % |
| 8 | **`reasoning_effort=low`** | **0.40** | 56.0 | **140** | 365 | **24.71 s** | 96 % |
| 8 | thinking off (`thinking`) | 0.20 | 88.8 | 444 | 281 | 71.60 s | 97 % |
| 32 | default | 1.27 | 522.6 | 410 | 291 | 42.80 s | 91 % |
| 32 | **`reasoning_effort=low`** | **2.23** | 312.1 | **140** | 347 | **18.74 s** | 88 % |
| 32 | thinking off (`thinking`) | 1.27 | 504.8 | 396 | 288 | 43.42 s | 90 % |

## Reading

**`reasoning_effort=low` is the control that works here.** Tokens per answer fall from
410 to 140, answers per second rise from 1.27 to 2.23 at concurrency 32, and median
latency drops from 42.80 s to 18.74 s. Characters per answer go **up**, 291 to 347 — the
shorter trace leaves more of the budget for the answer.

**The chat-template switch is inert, and the table shows it rather than asserting it.**
The `thinking off` rows are indistinguishable from the default rows: 1.27 answers per
second in both, 396 against 410 tokens per answer, 43.42 s against 42.80 s. A key the
template never reads is accepted by the server and changes nothing. Had this row been
omitted, the claim "this model has no template switch" would rest on reading the
template; with it, the measurement says the same thing.

> **This is exactly reversed from the Gemma-4 checkpoints.** There
> [`enable_thinking` works and `reasoning_effort` is inert](../../../gemma-4-26b-a4b/llama-cpp/scenarios/reasoning-cost.md);
> here the top-level parameter works and the template switch is absent. Two mechanisms,
> two models, no overlap — and both accept the wrong one without complaint.

**Utilisation stays at 88–97 % in every variant**, including the ones that shorten the
output. The card keeps working regardless of how much of the generation is trace, which
is consistent with this model running without speculative decoding.

## Not measured

- `reasoning_effort` at settings other than `low` — the protocol tests one step, and
  whether `medium` or a disable value exists on this checkpoint was not explored
- Answer quality at reduced effort. Characters per answer rise; whether the answers hold
  up is a separate question
- Whether the missing template switch is an omission in this GGUF conversion or in the
  upstream checkpoint
