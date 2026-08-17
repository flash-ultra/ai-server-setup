# Scenario: reasoning cost — vLLM B12X

What the thinking switches cost, and why this server cannot report the reasoning share.

**Setup:** [vLLM B12X TP=2](../README.md) · `nvidia/DeepSeek-V4-Flash-NVFP4` ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-17

## Method

Protocol `v1`, `--scenario reasoning`: concurrency 8 and 32, three variants each — the
server default, `reasoning_effort: low`, and thinking disabled via
`chat_template_kwargs`. The disable key is `thinking`, which is the protocol default and
the correct one for DeepSeek-V4; `enable_thinking` is the Gemma-4 spelling and would be
[silently ignored](../../../../README.md#switches-that-a-model-does-not-know-are-accepted-not-rejected).
Everything else pinned: `max_tokens` 512, 40 s per level, 3 discarded warmups, `usage`
counting.

The server runs `--reasoning-parser deepseek_v4`.

## Measurement

| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | p50 | GPU |
|---|---|---|---|---|---|---|---|---|
| 8 | default | 2.38 | 99.4 | 42 | 0 % | 259 | 3.43 s | 60 % · 41 % |
| 8 | `reasoning_effort: low` | 1.45 | 274.4 | 189 | 0 % | 238 | 5.70 s | 58 % · 66 % |
| 8 | thinking off | 2.27 | 92.8 | 41 | 0 % | 251 | 3.39 s | 64 % · 40 % |
| 32 | default | 4.08 | 168.4 | 41 | 0 % | 254 | 8.00 s | 88 % · 32 % |
| 32 | `reasoning_effort: low` | 2.48 | 462.9 | 187 | 0 % | 241 | 13.74 s | 74 % · 50 % |
| 32 | thinking off | 4.33 | 174.4 | 40 | 0 % | 250 | 7.53 s | 89 % · 37 % |

## Reading

**The 0 % reasoning column is a reporting gap, not a measurement.** This server returns
`completion_tokens_details` empty — the same response also carries
`prompt_tokens_details: None` — so `reasoning_tokens` is unavailable and the protocol's
reasoning share reads as zero for every variant. Total `completion_tokens` is reported
correctly, so throughput and tokens-per-answer in the table are sound; only the split
between thinking and answer is missing.

It is this build, not the tooling. The
[SGLang stack on the same machine](../../../deepseek-v4-flash-0731/sglang/scenarios/reasoning-cost.md),
queried through the same gateway minutes after these runs, answers with
`completion_tokens_details: {reasoning_tokens: 40, text_tokens: 3}` on a 43-token reply —
the field the protocol reads, populated, on the same host with the same client.

The characters-per-token ratio recovers the split well enough to prove the tokens exist:

| Variant | Tokens/answer | Chars/answer | Chars per token |
|---|---|---|---|
| default | 41 | 254 | 6.2 |
| `reasoning_effort: low` | 187 | 241 | **1.3** |
| thinking off | 40 | 250 | 6.3 |

Visible answers are the same length in all three variants — about 250 characters — but
`reasoning_effort: low` spends 187 tokens producing them against 40. Roughly **146 tokens
per answer generate no visible text**, which is what reasoning tokens are. They are being
generated and billed; they are just not being labelled.

**`reasoning_effort: low` costs 39–40 % of the answers per second and buys nothing
visible.** 2.38 → 1.45 at concurrency 8, 4.08 → 2.48 at 32, for an answer that is the same
length and, on this prompt, no more detailed. Output tokens per second nearly triples,
which is exactly the trap the protocol's `usage` rule exists to catch: a tokens-per-second
chart would rank this variant as the winner while it serves 40 % fewer users.

**Setting `thinking: false` changes almost nothing here.** 2.38 → 2.27 at concurrency 8
(within the run-to-run spread this stack shows) and 4.08 → 4.33 at 32. That is a different
result from the same switch on the older release, where SGLang serving
`DeepSeek-V4-Flash-0731` gained **3.5× the answers per second** with thinking off. The
reason is visible in the token counts: on this checkpoint the default already produces
41-token answers with no reasoning prelude, so there is nothing for the switch to turn
off. The 0731 comparison had 96 % of its tokens inside the thinking block.

**So the server default is already the cheap mode.** The expensive mode has to be asked
for by name, and asking for the cheap one explicitly is a no-op.

## Not measured

- Whether `reasoning_effort` at `medium` or `high` produces better answers for its cost.
  Only `low` was run, and only against the default
- Answer quality in any variant. The table measures length and throughput; that
  `reasoning_effort: low` adds no visible detail is an observation about one prompt at one
  answer length, not an evaluation
- Whether `reasoning_content` is populated in the response body even though
  `reasoning_tokens` is not. The parser is configured, so the text may well be split
  correctly while only the usage accounting is missing — a single non-streaming request
  with a thinking-heavy prompt would settle it
