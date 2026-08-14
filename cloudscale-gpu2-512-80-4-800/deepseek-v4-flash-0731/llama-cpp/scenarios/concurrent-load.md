# Scenario: concurrent load — llama.cpp

Concurrency sweep from 1 to 32 parallel requests. This is where the layer-split
ceiling becomes visible.

**Setup:** [llama.cpp layer-split](../README.md) · DeepSeek-V4-Flash-0731 UD-Q8_K_XL ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-14

## Method

Prompt ~1000 tokens, `max_tokens` 200, 40 s per concurrency level, GPU utilisation
sampled per card throughout. The server runs `-np 8` — eight slots of 131,072 tokens
each.

## Results

| Concurrent | Output tok/s | Req/s | TTFT p50 | GPU utilisation |
|---|---|---|---|---|
| 1 | 85.0 | 0.42 | 0.05 s | 21 · 21 · 22 · 25 % |
| 4 | 175.0 | 0.88 | 0.18 s | 20 · 19 · 19 · 21 % |
| 8 | 190.3 | 1.10 | 0.24 s | 21 · 19 · 20 · 22 % |
| 16 | 246.3 | 1.40 | 0.31 s | 22 · 21 · 20 · 21 % |
| 32 | 316.1 | 1.73 | **13.71 s** | 22 · 19 · 19 · 20 % |

## Reading

**The working range ends at 16.** Up to that point response time stays at 0.3 seconds.
At 32 all eight slots are occupied, requests queue, and the wait for the first token
jumps to 13.7 seconds — a 44× step, not a gradual degradation.

**Utilisation never moves.** 19–22 % per card at every level, from one request to 32.
Load does not fill the idle capacity because the cards work sequentially through the
layers; adding requests adds queueing, not parallel compute. This is the
[layer-split ceiling](../README.md#the-ceiling-no-tensor-parallelism), and no parameter
in this setup changes it.

**Throughput still grows, just slowly.** 85 → 316 output tok/s across the sweep is a
3.7× gain for 32× the load. For comparison,
[SGLang on the same hardware](../../sglang/scenarios/concurrent-load.md) delivers
1571 output tok/s at concurrency 32 and keeps TTFT at 0.25 s.

## Not measured

The one open knob for this workload shape — whether `-np` above 8 moves the cliff at
concurrency 32 or merely spreads the same starved compute across more queues — was
[not planned](../README.md#not-planned) when the series was cut short. Nothing else
here is untested: the sweep covers the full range the eight slots can serve.
