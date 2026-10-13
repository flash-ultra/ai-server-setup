# Scenario: long context — vLLM, MiMo build

Needle-in-a-haystack at 44,000 tokens.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens 44000`
instead of the default 960,000. The served context is 49,152, so 44,000 is roughly 90 % of
the window — the deepest point this setup can be tested at without changing the
configuration.

**This is not the depth the other models on this machine were measured at.** They used
180,000, which does not fit here. The needle result is comparable across models, the
prefill figures are not.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Prompt | 0.31 MB, 2,200 sentences at 20.00 tokens each |
| Prefill (TTFT) | 5.9 s |
| Prefill throughput | **7436 tok/s** |
| Total duration | 6.3 s |
| GPU utilisation | **100 % · 100 %** |
| Needles recovered | **3 of 3** `['XR-4471', 'QT-8829', 'ZB-1503']` |

## Reading

**All three needles, middle one included.** That is the one the scenario exists to test:
a model attending only to the edges of its context recovers the outer two and loses the
one at 50 %.

**7436 tok/s prefill, with both cards at 100 %.** For reference on the same machine,
[DeepSeek-0731 under SGLang](../../../deepseek-v4-flash-0731/sglang/scenarios/long-context.md)
measures 8227 tok/s at 64k and 7133 at 180k. MiMo sits inside that band — but at a quarter
of the depth, so this is not evidence that it would hold the rate deeper.

**Both cards saturated during prefill.** Prefill is the compute-heavy phase and the one
where tensor parallelism pays. This setup holds 100 % on both cards here and at every
level of [concurrent load](concurrent-load.md); DeepSeek runs 91–99 % under the same
protocol.

## Not measured

- **Anything deeper than 44,000 tokens.** The served window ends at 49,152, and the real
  ceiling of this configuration is [unresolved](../README.md#still-open).
- **Warm prefill.** This was the first long request the server saw. What a repeat against
  the same context costs is unmeasured.
- **Depths below 44,000.** The curve between short prompts and this point is not mapped,
  so prefill throughput at intermediate depth is unknown.
