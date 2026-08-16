# Scenario: concurrent load — llama.cpp

Concurrency sweep on a single card, plus a non-uniform prompt mix.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-26B-A4B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1` — prompt verbatim from `bench.py`, `max_tokens` 512, 40 s per level, 3
discarded warmups, counts from the `usage` fields.

**Deviation:** levels `1,4,8,16,32` via `--levels` instead of the pinned series. The
server runs 16 slots (`-np 16`, `-c 32768`, 2048 tokens per slot); above that the sweep
measures the queue rather than parallelism, and level 32 is included to show exactly
that transition. The other three cards were idle throughout.

## Throughput

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.38 | 190.1 | 649.9 | 2.76 s | 2.92 s | 88 % |
| 4 | 0.72 | 367.5 | 1256.4 | 5.87 s | 6.36 s | 74 % |
| 8 | 1.00 | 499.9 | 1726.0 | 9.17 s | 10.47 s | 66 % |
| 16 | 1.25 | 625.3 | 2157.8 | 14.62 s | 16.68 s | 59 % |
| 32 | **1.60** | **816.9** | **2778.5** | 29.11 s | 38.07 s | 49 % |

GPU column is the card this model ran on; the other three read 0 % and are omitted.

## Prompt mix

Five request shapes at concurrency 32, drawn at random per request.

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 1.60 | 815.9 | 2777.5 | 28.98 s | 37.23 s |
| **mixed** | **1.52** | 780.8 | 1015.9 | 25.64 s | 35.47 s |

## Reading

**Throughput scales monotonically to 32 and had not flattened.** Output tokens rise
190 → 368 → 500 → 625 → 817 across the sweep, and answers per second follow. The
dense [Gemma-4-31B](../../../gemma-4-31b/llama-cpp/scenarios/concurrent-load.md) on the
same card and configuration stalls between 8 and 16; this one does not.

**Latency stays usable much longer.** p50 at 32 concurrent is 29.11 s against 113.78 s
for the dense model — a 3.9× difference at the same load, on the same hardware, with the
same engine.

**GPU utilisation falls as load rises — 88 % down to 49 %**, where the SGLang stack with
DeepSeek-V4 holds 90–97 % on every level. Speculative decoding is not the reason: a
[control run of this model with MTP disabled](../README.md#mtp-helps-throughput-and-does-not-explain-the-utilisation-curve)
falls the same way, 89 % to 58 %.

The reason is llama.cpp's batching. The [engine comparison](../../engine-comparison.md)
serves this same model on this same card under vLLM at **100 % on every level** and 5.9×
the answers per second — which rules out the model as the explanation, since it is the
same model.

Two theories were tried and discarded on the way there: speculative decoding (refuted by
the control run above) and compute-per-token, on the grounds that a 4 B-active forward
pass cannot fill a card (refuted by vLLM filling it with exactly that model). What the
dense [Muse Glimmer](../../../muse-glimmer-30b/llama-cpp/scenarios/concurrent-load.md)
run does show — 92 % utilisation and **less** throughput, 520.5 against 816.9 — is that a
model heavy enough per token hides the gaps this scheduler leaves.

**A realistic prompt mix costs 5 %.** Answers per second drop from 1.60 to 1.52, and p50
actually improves slightly because the mix contains shorter requests. Total tokens per
second fall much further (−63 %) for the same reason — that spread is an artefact of the
mix, not a performance signal.

## Not measured

- Concurrency above 32 with a slot count to match. 16 slots was chosen to fit the same
  configuration on all three models; this model had 42 GB of card left and would carry
  more
- Whether the utilisation curve recovers without MTP at levels above 32 — the control
  run covers the same 1–32 range
- Sustained load beyond 40 s per level
