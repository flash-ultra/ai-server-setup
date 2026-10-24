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
| 8 | default | 4.67 | 320.2 | 68 | 23 % | 314 | 1.68 s |
| 8 | `reasoning_effort=low` | 4.80 | 324.1 | 68 | 21 % | 317 | 1.64 s |
| 8 | thinking off (`enable_thinking`) | **6.83** | 320.2 | 47 | **0 %** | 290 | **1.18 s** |
| 32 | default | 10.32 | 706.2 | 68 | 23 % | 314 | 3.12 s |
| 32 | `reasoning_effort=low` | 10.35 | 705.7 | 68 | 22 % | 318 | 3.09 s |
| 32 | thinking off (`enable_thinking`) | **14.72** | 703.6 | 48 | **0 %** | 293 | **2.16 s** |

An earlier series at a 49,152 window matched every row except `default` at concurrency 8,
where it read 3.75 answers/s — below its own `reasoning_effort=low` arm, which never made
sense. That value was an outlier; the ordering here is the reproducible one.

## Reading

**Switching thinking off buys 43 % more answers and 31 % less latency at no cost in token
rate.** At concurrency 32: 10.32 → 14.72 answers/s and 3.12 → 2.16 s, while output tokens
per second stay flat at 706.2 → 703.6. The machine was already saturated; the same tokens
simply get spent on answers instead of scratchpad. That is the clean form of this
trade-off and it is not what the other models here do — DeepSeek's thinking arm *raises*
tokens per second while cutting answers by a factor of four.

**`reasoning_effort=low` does not reduce reasoning.** 21–23 % in both the default and the
`low` row, 68 tokens per answer in both. At concurrency 32 it is indistinguishable from
the default (10.35 against 10.32). The parameter is accepted; it
moves nothing worth measuring. Only `reasoning_effort: "none"` and
`enable_thinking: false` reach zero.

**Thinking here is cheap in absolute terms.** 23 % of 68 tokens is roughly 16 tokens of
scratchpad per answer. DeepSeek with thinking on spends 85 % of 290. That is the whole
reason MiMo can be measured with thinking on and still lead the
[concurrency ladder](concurrent-load.md) — its thinking arm is not a different operating
point, it is the same one with a short preamble.

**Visible output shrinks by 7 % when thinking is off**, 314 → 293 characters. Whether
those 21 characters are worth 43 % of the answer rate is a quality question this scenario
cannot answer. The [quality battery](../../README.md#quality-checks-outside-the-protocol) was run
with thinking on.
