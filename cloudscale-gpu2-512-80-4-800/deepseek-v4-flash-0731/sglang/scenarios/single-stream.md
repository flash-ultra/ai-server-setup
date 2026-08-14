# Scenario: single stream — SGLang

One request at a time, no competing load. This is the interactive single-user case.

**Setup:** [SGLang + SM120 patchset](../README.md) · DeepSeek-V4-Flash-0731 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-15

## Method

Prompt ~1000 tokens, `max_tokens` 512, 40 s at concurrency 1, token counts from the
`usage` fields. The TTFT figure comes from the separate latency run with shorter
output described in [concurrent-load.md](concurrent-load.md).

## Results

| Metric | Value |
|---|---|
| Output | 131.2 tok/s |
| Total (incl. reasoning) | 665.2 tok/s |
| Requests | 0.28 req/s |
| Latency p50 | 3.81 s |
| TTFT p50 | 0.15 s |
| GPU utilisation | 92 · 92 · 92 · 91 % |

## Reading

**A single stream already occupies all four cards.** Utilisation sits above 90 % at
concurrency 1, because tensor, data and expert parallelism spread every forward pass
across the cards rather than walking through them.

**Total tokens are five times output tokens.** 665 versus 131 tok/s is the reasoning
share: 96 % of what the model generates never reaches the visible answer. A
single-user session therefore costs roughly five times what the answer length
suggests.

**Single-stream speed is not where this stack wins.** llama.cpp reaches
[91 tok/s single-stream](../../llama-cpp/scenarios/single-stream.md) with a lower TTFT
of 0.05 s. Decode here is interconnect-latency bound, and this machine has no NVLink.
The advantage appears under [concurrent load](concurrent-load.md).

## Not measured

Nothing open for this workload shape. The remaining gaps on this setup are
configuration and correctness rather than measurement, and are tracked in the
[setup README](../README.md#still-open).
