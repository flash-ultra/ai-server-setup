# Scenario: concurrent load — llama.cpp

Concurrency sweep on a single card, plus a non-uniform prompt mix.

**Setup:** [llama.cpp single-card](../README.md) · Gemma-4-31B-it BF16 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-16

## Method

Protocol `v1` — prompt verbatim from `bench.py`, `max_tokens` 512, 40 s per level, 3
discarded warmups, counts from the `usage` fields.

**Deviation:** levels `1,4,8,16,32` via `--levels`. The server runs 16 slots (`-np 16`,
`-c 32768`), so level 32 shows the queue rather than added parallelism. The other three
cards were idle throughout.

## Throughput

| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |
|---|---|---|---|---|---|---|
| 1 | 0.15 | 60.0 | 243.8 | 7.89 s | 8.35 s | 93 % |
| 4 | 0.40 | 156.0 | 646.4 | 10.85 s | 15.40 s | 80 % |
| 8 | 0.60 | 238.3 | 973.9 | 16.08 s | 21.01 s | 71 % |
| 16 | 0.60 | **230.0** | 965.6 | **40.57 s** | 43.60 s | 70 % |
| 32 | 0.80 | 310.2 | 1291.0 | **113.78 s** | 135.92 s | **33 %** |

## Prompt mix

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 0.80 | 320.5 | 1301.3 | 110.55 s | 129.38 s |
| **mixed** | **0.70** | 354.5 | 453.6 | 107.31 s | 151.51 s |

## Reading

**Throughput stops scaling between 8 and 16 while latency more than doubles.** Output
tokens go 238.3 → 230.0 — flat within noise — but p50 rises from 16.08 s to 40.57 s.
Past that point the extra load buys nothing and costs everything; 16 concurrent requests
is where this configuration stops being useful.

**At 32 the card reads 33 % while p50 reaches 113.78 s.** Unlike the sparse sibling,
where low utilisation comes with high throughput, here both are poor at once — this is
the stall, and the utilisation number is a symptom rather than the finding. Speculative
decoding is not the cause; a
[control run on the sibling with MTP disabled](../../../gemma-4-26b-a4b/llama-cpp/README.md#mtp-helps-throughput-and-does-not-explain-the-utilisation-curve)
loses utilisation just as fast while still scaling.

**The MoE sibling is faster on every axis.**
[Gemma-4-26B-A4B](../../../gemma-4-26b-a4b/llama-cpp/scenarios/concurrent-load.md) on the
same card, same engine, same configuration: 2.6× the output tokens at concurrency 32
(816.9 against 310.2) and **3.9× better** median latency (29.11 s against 113.78 s), at
a comparable total parameter count. Comparing the two is the clearest argument in this
directory for choosing a sparse model when a single card has to serve load.

**A realistic prompt mix costs 13 %.** Answers per second 0.80 → 0.70. The much larger
drop in total tokens per second is an artefact of the mix containing shorter prompts.

## Not measured

- Concurrency above 32, and whether more slots would move the stall point
- The same sweep without MTP at levels above 1 — the control run in the setup README
  covers this model's sibling, not this one
- Sustained load beyond 40 s per level
