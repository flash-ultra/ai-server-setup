# Scenario: long context — SGLang TP=2

Needle-in-a-haystack at 180k tokens.

**Setup:** [SGLang TP=2](../README.md) · `DeepSeek-V4-Flash-0731` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens 180000`
instead of the default 960,000. Not a limit of the checkpoint — it serves 262,144 here and
is native to 1,048,576 — but the value
[MiniMax-M2.5 was measured at](../../../minimax-m2-5/vllm/scenarios/long-context.md), so
the two are directly comparable.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Prefill (TTFT) | 26.4 s |
| Prefill throughput | 6823 tok/s |
| Total duration | 26.6 s |
| GPU utilisation | 99 % · 99 % |
| Needles recovered | **3 of 3** `['XR-4471', 'QT-8829', 'ZB-1503']` |

## Reading

**2.6× the prefill throughput of MiniMax-M2.5** on the same cards and the same prompt:
6823 against 2580 tok/s, 26.4 s against 69.8 s to first token. For agent work with a large
standing context, that is the difference between a pause and a coffee break.

**All three needles, middle one included**, which is the one the scenario exists to test.

**The harness worked here, and that is itself a finding.** The same scenario against
MiniMax under vLLM reported
[0 of 3 and had to be corrected by hand](../../../minimax-m2-5/vllm/scenarios/long-context.md#the-harness-reported-0-of-3-the-model-recovers-all-three).
Under SGLang the streaming path returns the answer intact. **That narrows the open
`bench.py` bug to the vLLM combination** rather than to the scenario or to long prompts in
general — which was not knowable from a single engine.

## Not measured

- **The full 1M context.** `max_total_num_tokens` is 1,382,912, so one 1M request fits the
  pool arithmetically; concurrency would drop to one. Untested.
- **Recovery below 180k.**
- **A cold second run.** Prefill throughput here is a single measurement.
