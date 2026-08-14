# Scenario: concurrent load — SGLang

Concurrency sweep from 1 to 128 parallel requests: how throughput, latency and GPU
utilisation develop under load.

**Setup:** [SGLang + SM120 patchset](../README.md) · DeepSeek-V4-Flash-0731 ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-14/15

## Method

Prompt ~1000 tokens, `max_tokens` 512, 40 s per concurrency level, token counts from
the `usage` fields, GPU utilisation sampled per card throughout. The TTFT table below
comes from a separate run with shorter output — there what matters is how quickly the
first answer begins, not how much is produced.

## Throughput

| Concurrent | Output tok/s | Total tok/s | Req/s | Latency p50 | GPU |
|---|---|---|---|---|---|
| 1 | 131.2 | 665.2 | 0.28 | 3.81 s | 92 · 92 · 92 · 91 % |
| 8 | 631.0 | 3155.7 | 1.30 | 6.58 s | 93 · 92 · 93 · 93 % |
| 16 | 986.1 | 4918.6 | 2.02 | 8.67 s | 90 · 93 · 91 · 94 % |
| 32 | 1571.4 | 7785.8 | 3.20 | 11.81 s | 92 · 93 · 92 · 93 % |
| 64 | 2276.4 | 11258.2 | 4.62 | 17.56 s | 93 · 93 · 92 · 93 % |
| 128 | **2956.0** | **14656.5** | 6.03 | 29.82 s | 91 · 95 · 92 · 94 % |

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

**Throughput scales to 128, latency does not.** Total tokens per second keep rising
across the whole sweep, but response time grows with them — 3.8 s at one user against
29.8 s at 128. For interactive use the usable range is 32 to 64; beyond that you are
optimising for batch processing.

**TTFT stays flat where it matters.** Even at 64 concurrent requests the first token
arrives after 0.32 s. The queue shows up in total response time, not in time to first
token — the opposite of the llama.cpp behaviour, where TTFT jumps to 13.71 s once the
slots are full.

**Utilisation is constant at 90–95 %.** The cards are saturated at every level,
including concurrency 1, so the throughput gain across the sweep comes from better
batching rather than from idle capacity being filled.

## Not measured

- Effect of lowering `reasoning_effort` on throughput — 96 % of generated tokens are
  reasoning, so this is the largest untested lever on cost per answer
- Behaviour under real agent traffic — the synthetic prompts here have a uniform shape,
  which overstates draft acceptance and with it output tok/s
- Concurrency above 128 — the sweep stops there, and the curve had not yet flattened
