# Scenario: long context — SGLang

The full 1,048,576-token context, run end to end. Not just whether it completes, but
whether the model reaches the whole range.

**Setup:** [SGLang + SM120 patchset](../README.md) · DeepSeek-V4-Flash-0731 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-15

## Method

A needle-in-a-haystack run at full length. Filler text was calibrated against the
server's own tokeniser (40 tokens per sentence, measured via `usage.prompt_tokens`),
then three distinct facts were planted at **10 %, 50 % and 90 %** of the context:

```
XR-4471   at 10 %
QT-8829   at 50 %
ZB-1503   at 90 %
```

The prompt closes with a request to name all three codes. Placing one needle
mid-context is deliberate: models that only attend to the beginning and end of a long
input will recover the outer two and miss the middle one.

Single request, streaming enabled so that time-to-first-token equals prefill
completion. VRAM and GPU utilisation sampled every 2 s throughout.

## Results

| Metric | Value |
|---|---|
| Prompt | 3.50 MB, ~960,000 tokens |
| **Prefill (TTFT)** | **470.7 s** (7:51 min) |
| Prefill throughput | 2039 tok/s |
| Total duration | 473.5 s |
| Generated | 62 tokens |
| VRAM peak | 87,153 / 88,265 / 87,217 / 87,151 MiB |
| GPU utilisation (mean) | 67 / 72 / 66 / 69 % |
| **Needles recovered** | **3 of 3, exact** |

Answer returned: `XR-4471, QT-8829, ZB-1503`

The server stayed `healthy` throughout and continued serving afterwards without a
restart.

## Reading

**Retrieval is intact across the full range.** All three codes came back exactly,
including the one at mid-context. There is no "lost in the middle" degradation at this
length — the 1M window is usable, not just configurable.

**Prefill dominates completely.** 470.7 s of the 473.5 s total went into processing
the prompt; generating the answer took under 3 seconds. At full context the input, not
the output, is the entire cost.

**Eight minutes makes this batch work, not interactive.** A cold full-length prompt
means the user waits nearly eight minutes for the first character. Repeated queries
against the same context hit the radix prefix cache and skip this, so the pattern that
works is: load a large corpus once, then ask many questions against it.

**A single prefill does not saturate the cards.** Utilisation averaged 66–72 %, against
92 % under [concurrent load](concurrent-load.md). One long prefill leaves capacity
unused — consistent with the prefill-scheduling bottleneck documented for DP attention,
where decode work stalls behind prefill chunks on ranks that share neither.

**Prefill throughput is roughly half the published figure.** 2039 tok/s here against
~4315 tok/s reported for a 512K prefill on the reference configuration. The run was
cold with no prefix cache, and throughput is known to decay with depth, so both effects
point the same way — but the gap is large enough to be worth a second look.

## Comparison

llama.cpp was never run at full length; its
[long-context scenario](../../llama-cpp/scenarios/long-context.md) stops at 128k, where
prompt processing had already fallen to 736 tok/s. Extrapolating that curve to 1M
suggests well over an hour of prefill, against the 7:51 measured here.

## Not measured

- Warm run against the same context to quantify the prefix-cache benefit
- Intermediate depths (256k, 512k) to map the prefill decay curve
- Whether `SGLANG_SM120_INDEXER_SPLIT` is actually engaging at this length
- Concurrent long-context requests — the reference recipe advises keeping concurrency
  at or below 32 for cold large contexts
