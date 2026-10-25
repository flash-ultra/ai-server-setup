# Scenario: concurrent load — vLLM + EXL3, TP=2

The protocol ladder from 1 to 256 against a setup whose default slot count is 8.

**Setup:** [vLLM + EXL3 plugin, TP=2](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3
3 bpw · [cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-25

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations. `bench.py --scenario
concurrent`, against the engine on `127.0.0.1:8010`, measurement configuration
(1 M window, 4.25 GiB KV), nothing else on the cards. Default thinking arm.

**`--max-num-seqs` was left at the pack's default of 8.** The ladder was run to 256
anyway, because the protocol's levels are fixed and because the shape of the result is
worth having — but every level above 8 measures queueing, not batching. That is stated
here rather than silently dropped, and it is the reason the rows below are not placed
beside other models' concurrency figures without the caveat.

**One run.**

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.85 | 140.7 | 1194.7 | 1.18 s | 1.80 s | 96 % · 98 % |
| 8 | 1.57 | 261.0 | 2214.0 | 4.85 s | 8.53 s | 87 % · 92 % |
| 16 | 1.88 | 299.4 | 2624.4 | 10.05 s | 12.39 s | 84 % · 90 % |
| 32 | 2.17 | 376.4 | 3073.4 | 20.93 s | 25.31 s | 85 % · 90 % |
| 64 | 2.95 | 488.1 | 4146.1 | 40.46 s | 45.21 s | 83 % · 89 % |
| 128 | 4.58 | 751.1 | 6424.1 | 63.93 s | 87.73 s | 81 % · 88 % |
| 256 | 7.88 | 1296.0 | 11061.0 | 105.62 s | 174.06 s | 81 % · 87 % |

**Prompt mix at concurrency 32**

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 2.20 | 372.8 | 3100.8 | 20.87 s | 24.68 s |
| mixed | 1.38 | 671.8 | 1780.5 | 45.34 s | 52.82 s |

## Reading

**The curve is monotone and the latency is the price.** Output throughput rises 9.2×
from concurrency 1 to 256 while p50 rises 90×. Past the eight slots the engine is not
batching harder, it is holding a queue — 256 requests through 8 slots at roughly 0.9 s
of service each is the 105 s median almost exactly.

**GPU utilisation falls as concurrency rises**, 96–98 % at one request down to 81–87 %
at 256. That is the opposite of every other setup on this machine and the clearest
evidence that the ladder is not measuring saturation: a queued request consumes no GPU.
A single stream already keeps both cards near full, because a 3-bit 763 B MoE with
speculative decoding has enough work in one sequence.

**This is not a figure to compare against the machine's other concurrency rows.** With
8 slots against vLLM's default of 256 and SGLang's dynamic pool, the number below says
what this *configuration* does, not what the model can do. The production setup runs
32 slots; that configuration has not been put through the ladder.

**The mixed-prompt row is the useful one for planning.** Varying prompt length at the
same concurrency moves output throughput up 80 % (372.8 → 671.8) and answers per second
down 37 %, because long prompts occupy a slot for longer while producing more tokens.
With few slots, prompt-length variance costs more than it does with many.

## Against the rest of the machine

At concurrency 256, thinking on, all two-card setups:

| | Output tok/s | Answers/s | Tok/answer | p50 |
|---|---|---|---|---|
| [DeepSeek-0731](../../../deepseek-v4-flash-0731/) · SGLang | **3,584** | 10.97 | 327 | 27.58 s |
| [MiMo](../../../mimo-v2-6-flash/) · vLLM | 3,129 | **46.05** | 68 | **5.74 s** |
| [MiniMax](../../../minimax-m2-5/) · vLLM | 2,947–3,126 | 9.65–9.75 | 302–324 | 57.34 s |
| [Qwen 27 B](../../../qwen3-8-27b/) · vLLM | 1,821 | 9.43 | 193 | 34.89 s |
| **this setup** · 8 slots | 1,296 | 7.88 | 165 | 105.62 s |

**Last on every column, and the slot count explains it rather than the model.** The
machine's own
[finding on server slots](../../../../README.md#more-server-slots-lower-latency-without-raising-the-ceiling)
predicts exactly this shape: slot count sets how fast saturation is reached and leaves
the ceiling alone, with the latency curves separating far more than the throughput ones.
Here it is a factor of 18 in p50 against MiMo and a factor of 2.8 in tokens per second.

The pack is built for a few long agentic sessions rather than for fan-out, and this is
what that choice costs when the workload is the opposite.
