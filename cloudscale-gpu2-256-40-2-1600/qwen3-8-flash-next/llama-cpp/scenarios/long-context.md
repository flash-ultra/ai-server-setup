# Scenario: long context — llama.cpp master

Needle-in-a-haystack at 180k tokens.

**Setup:** [llama.cpp `-sm layer`](../README.md) · `Qwen3.8-Flash-Next` UD-Q5_K_XL ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-31

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens 180000`
instead of 960,000, the same value the
[other two models on this machine](../../../deepseek-v4-flash-0731/sglang/scenarios/long-context.md)
were measured at, so the three are comparable.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Prefill (TTFT) | 134.0 s |
| Prefill throughput | 1343 tok/s |
| Total duration | 137.8 s |
| GPU utilisation | 55 % · 61 % |
| Needles recovered | **3 of 3** `['XR-4471', 'QT-8829', 'ZB-1503']` |

## Reading

**All three needles, and the harness reported them correctly.** The
[streaming defect](../../../minimax-m2-5/vllm/scenarios/long-context.md#the-harness-reported-0-of-3-the-model-recovers-all-three)
that forced a manual correction under vLLM does not appear here, as it did not under
SGLang. Two engines clean, one affected — the fault is in the vLLM combination.

**Prefill utilisation reaches 55–61 %, against 45 % everywhere else.** Prefill
parallelises across the layer split better than decode does. It is the only measurement in
this directory where the second card contributes meaningfully.

**2.5× GLM-5.3-Flash on the same engine**, 1343 against ~530 tok/s — and still a fifth of
[DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/long-context.md) at 6823.
Two minutes to first token against twenty-six seconds for the same prompt.

## Not measured

- **The full 262,144 context.**
- **A second run.** Prefill here is a single measurement.
