# Scenario: concurrent load — llama.cpp

Concurrency sweep on a single card, plus a non-uniform prompt mix.

**Setup:** [llama.cpp single-card](../README.md) · Muse-Glimmer-30B BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1`, levels `1,4,8,16,32` via `--levels` (16 slots, `-c 32768`, `-np 16`).
The other three cards were idle throughout.

**No speculative decoding.** The GGUF package for this model carries no MTP file, so it
runs without `--spec-type`. That is not a tuning choice — it is what makes this sweep
the control against the two Gemma runs, which do speculate.

## Throughput

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.07 | 28.6 | 123.6 | 14.93 s | 14.93 s | **99 %** |
| 4 | 0.30 | 123.0 | 503.1 | 19.01 s | 24.47 s | 96 % |
| 8 | 0.50 | 200.1 | 833.6 | 21.02 s | 29.88 s | 94 % |
| 16 | 0.93 | 368.8 | 1540.7 | 24.80 s | 58.20 s | 93 % |
| 32 | 1.27 | 520.5 | 2135.9 | 42.01 s | 67.17 s | **92 %** |

## Prompt mix

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 1.30 | 519.3 | 2166.4 | 41.69 s | 62.79 s |
| **mixed** | **1.07** | 550.4 | 753.3 | 51.48 s | 70.20 s |

## Reading

**Utilisation stays between 92 and 99 % across the entire sweep**, where both Gemma
models on the same card, engine and slot configuration fall to 49 % and 33 % at
concurrency 32.

Speculative decoding was the obvious suspect, since this model runs without it and both
Gemmas speculate — and it is the wrong answer. A
[control run of Gemma-4-26B-A4B with MTP disabled](../../../gemma-4-26b-a4b/llama-cpp/README.md#mtp-helps-throughput-and-does-not-explain-the-utilisation-curve)
loses utilisation just as fast: 89 % at concurrency 1 down to 58 % at 32.

The cause is llama.cpp's batching, established in the
[engine comparison](../../../gemma-4-26b-a4b/engine-comparison.md): vLLM serves the
sparse Gemma on the same card at 100 % utilisation, so neither speculation nor the model
explains the gaps.

What this run adds is why they do not show here. A dense 30 B model does far more work
per forward pass than one with 4 B active parameters — 28.6 tokens per second against
190.1 — so the scheduler's idle windows are hidden behind compute rather than exposed by
it. **High utilisation is not the same as high throughput:** the sparse model delivers
816.9 output tokens per second at 49 % against this model's 520.5 at 92 %.

**Throughput scales monotonically and latency degrades gently.** 28.6 → 520.5 output
tokens per second across the sweep, with p50 rising only from 14.9 s to 42.0 s — a
2.8× latency cost for an 18× throughput gain.

**Single-stream is the slowest of the three models measured here.** 28.6 tokens per
second against 60.0 for the dense
[Gemma-4-31B](../../../gemma-4-31b/llama-cpp/scenarios/concurrent-load.md) and 190.1 for
the [MoE sibling](../../../gemma-4-26b-a4b/llama-cpp/scenarios/concurrent-load.md). Part
of that gap is the missing speculation — the Gemmas gain 37–49 % from MTP at low
concurrency — and part is the dense 30 B architecture.

**The order reverses under load.** At concurrency 32 this model delivers 520.5 output
tokens per second against 310.2 for the dense Gemma, despite being slower at every low
level. Holding the card full matters more than per-token speed once the queue is deep.

**A realistic prompt mix costs 18 %** — the largest of the three, 1.30 down to 1.07
answers per second, and the only one where p50 also worsens.

## Not measured

- Speculative decoding for this model. `meta-models/Muse-Glimmer-30B-assistant` exists
  as a draft checkpoint but is not in the GGUF package used here, so MTP was never on
- Concurrency above 32
- Sustained load beyond 40 s per level
