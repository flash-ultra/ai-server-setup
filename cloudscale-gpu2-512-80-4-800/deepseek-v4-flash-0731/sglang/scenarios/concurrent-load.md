# Scenario: concurrent load — SGLang

Concurrency sweep from 1 to 256 parallel requests: how throughput, latency and GPU
utilisation develop under load, and what a non-uniform prompt mix costs.

**Setup:** [SGLang + SM120 patchset](../README.md) · DeepSeek-V4-Flash-0731 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-14/15

## Method

Prompt ~1000 tokens, `max_tokens` 512, 40 s per concurrency level, token counts from
the `usage` fields, GPU utilisation sampled per card throughout. The TTFT table below
comes from a separate run with shorter output — there what matters is how quickly the
first answer begins, not how much is produced.

The levels above 128 were measured in a later run; they use the same prompt and method
but sample GPU utilisation as a single mean across all four cards.

## Throughput

| Concurrent | Output tok/s | Total tok/s | Req/s | Latency p50 | GPU |
|---|---|---|---|---|---|
| 1 | 131.2 | 665.2 | 0.28 | 3.81 s | 92 · 92 · 92 · 91 % |
| 8 | 631.0 | 3155.7 | 1.30 | 6.58 s | 93 · 92 · 93 · 93 % |
| 16 | 986.1 | 4918.6 | 2.02 | 8.67 s | 90 · 93 · 91 · 94 % |
| 32 | 1571.4 | 7785.8 | 3.20 | 11.81 s | 92 · 93 · 92 · 93 % |
| 64 | 2276.4 | 11258.2 | 4.62 | 17.56 s | 93 · 93 · 92 · 93 % |
| 128 | 2956.0 | 14656.5 | 6.03 | 29.82 s | 91 · 95 · 92 · 94 % |
| 192 | 4287.5 | 21425.6 | 8.82 | 27.70 s | 97 % |
| 256 | **5420.7** | **27025.5** | **11.12** | 31.15 s | 97 % |

The second run repeated concurrency 128 and measured 3138.2 output tok/s against
2956.0 in the first — about 6 % run-to-run variation at this level.

## Prompt mix

The sweep above uses one prompt shape repeatedly. Real agent traffic does not. This
run mixes five shapes at concurrency 32 — a short factual question, a code review, a
long analysis (~4500 tokens), a tool-call formulation, and mid-length prose — drawn at
random per request.

| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |
|---|---|---|---|---|---|
| uniform | 3.12 | 1535.2 | 7603.9 | 11.94 s | 13.91 s |
| **mixed** | **2.52** | 1292.8 | 5026.3 | 13.95 s | 17.00 s |
| mixed, thinking off | 2.95 | 1292.1 | 5899.8 | 12.62 s | 16.60 s |

## Latency under load

Shorter output, same concurrency levels.

| Concurrent | Req/s | TTFT p50 | TTFT p95 |
|---|---|---|---|
| 1 | 0.62 | 0.15 s | 0.15 s |
| 8 | 2.12 | 0.18 s | 2.09 s |
| 16 | 3.83 | 0.20 s | 0.62 s |
| 32 | 5.55 | 0.25 s | 0.62 s |
| 64 | 7.95 | **0.32 s** | 0.97 s |

## GPU utilisation at 32 concurrent requests

Against [llama.cpp](../../llama-cpp/scenarios/concurrent-load.md) on the same hardware
with the same weights:

```
SGLang     GPU0 ████████████████████░  92 %
           GPU1 ████████████████████░  93 %
           GPU2 ████████████████████░  92 %
           GPU3 ████████████████████░  93 %

llama.cpp  GPU0 ████░░░░░░░░░░░░░░░░░  22 %
           GPU1 ████░░░░░░░░░░░░░░░░░  19 %
           GPU2 ████░░░░░░░░░░░░░░░░░  19 %
           GPU3 ████░░░░░░░░░░░░░░░░░  20 %
```

llama.cpp distributes layers across cards and works through them sequentially; SGLang
distributes tensors and has all four compute at once.

## Reading

**Throughput keeps scaling to 256 — the curve does not flatten.** From 128 to 256 both
output and total tokens rise by 73 %, and answers per second nearly double. This
contradicts the reference recipe for this image, which reports throughput regressing
beyond concurrency 128. On this machine 256 is the best measured level, and it is also
the configured `max_running_requests`, so the true ceiling may lie higher still.

**Latency is what breaks first, not throughput.** p95 doubles from 32.70 s at 128 to
53.59 s at 256 while p50 barely moves — the tail stretches rather than the median. For
interactive use the usable range remains 32 to 64; the levels above that are batch
territory.

**TTFT stays flat where it matters.** Even at 64 concurrent requests the first token
arrives after 0.32 s. The queue shows up in total response time, not in time to first
token — the opposite of the llama.cpp behaviour, where TTFT jumps to 13.71 s once the
slots are full.

**Utilisation is constant at 90–97 %.** The cards are saturated at every level,
including concurrency 1, so the throughput gain across the sweep comes from better
batching rather than from idle capacity being filled.

**A realistic prompt mix costs about 19 %.** Answers per second drop from 3.12 to 2.52
and p95 latency rises by 22 % when request shapes vary. The synthetic sweep therefore
flatters the numbers — but moderately, not dramatically. Total tokens per second fall
further (−34 %) than output tokens (−16 %), because the mix contains shorter prompts;
that spread is an artefact of the mix, not a performance signal.

## Not measured

- Concurrency above 256 — that is the configured `max_running_requests`; raising it
  would need a restart and the curve was still climbing
- Draft acceptance under the mixed traffic — the mix was measured end to end, but
  per-request acceptance was not recorded, so the assumed link between prompt
  uniformity and acceptance remains untested
- Sustained load beyond 40 s per level, which is where memory pressure and cache
  eviction would appear

The effect of thinking on cost per answer is measured separately in
[reasoning-cost.md](reasoning-cost.md).
