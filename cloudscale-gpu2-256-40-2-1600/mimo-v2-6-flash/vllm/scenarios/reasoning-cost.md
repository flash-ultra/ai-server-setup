# Scenario: reasoning cost — vLLM, MiMo build

What thinking costs per answer, and which switch actually moves it.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13

## Method

Protocol `v1`, `--scenario reasoning`, no deviations. Three variants at concurrency 8 and
32: the setup's default, `reasoning_effort=low`, and thinking disabled through
`chat_template_kwargs: {"enable_thinking": false}`.

**The key was verified before the run**, as the protocol requires. Five candidates were
sent against the same question and only two moved `reasoning_tokens` to zero; the
DeepSeek key `thinking` is among the three that are
[accepted and silently ignored](../README.md#thinking-can-be-switched-off-and-only-two-of-five-ways-work).
A run against that key would have reported "disabling thinking changes nothing", which is
a false negative rather than a result.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 |
|---|---|---|---|---|---|---|---|
| 8 | default | 3.75 | 256.1 | 68 | 22 % | 316 | 2.14 s |
| 8 | `reasoning_effort=low` | 4.88 | 325.2 | 67 | 22 % | 310 | 1.65 s |
| 8 | thinking off (`enable_thinking`) | **6.72** | 316.5 | 47 | **0 %** | 291 | **1.18 s** |
| 32 | default | 10.10 | 697.5 | 69 | 22 % | 320 | 3.15 s |
| 32 | `reasoning_effort=low` | 10.28 | 695.1 | 68 | 22 % | 312 | 3.10 s |
| 32 | thinking off (`enable_thinking`) | **14.78** | 695.5 | 47 | **0 %** | 290 | **2.18 s** |

## Reading

**Switching thinking off buys 46 % more answers and 31 % less latency at no cost in token
rate.** At concurrency 32: 10.10 → 14.78 answers/s and 3.15 → 2.18 s, while output tokens
per second stay flat at 697.5 → 695.5. The machine was already saturated; the same tokens
simply get spent on answers instead of scratchpad. That is the clean form of this
trade-off and it is not what the other models here do — DeepSeek's thinking arm *raises*
tokens per second while cutting answers by a factor of four.

**`reasoning_effort=low` does not reduce reasoning.** 22 % in both the default and the
`low` row, 67–68 tokens per answer against 68–69. At concurrency 32 it is
indistinguishable from the default (10.28 against 10.10). The parameter is accepted; it
moves nothing worth measuring. Only `reasoning_effort: "none"` and
`enable_thinking: false` reach zero.

**Thinking here is cheap in absolute terms.** 22 % of 68 tokens is roughly 15 tokens of
scratchpad per answer. DeepSeek with thinking on spends 85 % of 290. That is the whole
reason MiMo can be measured with thinking on and still lead the
[concurrency ladder](concurrent-load.md) — its thinking arm is not a different operating
point, it is the same one with a short preamble.

**Visible output shrinks by 8 % when thinking is off**, 320 → 290 characters. Whether
those 30 characters are worth 46 % of the answer rate is a quality question this scenario
cannot answer. The [quality battery](../../README.md#quality-checks-outside-the-protocol) was run
with thinking on.

## Not measured

- **`reasoning_effort` above `low`.** The protocol pins `low`.
- **`reasoning_effort: "none"`** as a scenario arm, although it was verified to work as a
  switch. The scenario uses `enable_thinking`.
- **Concurrency other than 8 and 32.**
- **Quality with thinking off.** Every quality result in this directory is thinking on.
