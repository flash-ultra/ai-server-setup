# Scenario: single stream — vLLM TP=2

One request at a time, no competing load. The interactive single-user case, both
thinking arms.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `Qwen3.8-27B` BF16 ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-24

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations. `bench.py --scenario
single`, run **on the machine against the engine on `127.0.0.1:8001`**, not through the
`api-router` — a Python hop in front would be in the number, and the setups this is
compared against had no router.

**The embedding model stayed loaded.** This measures the production configuration at
`--gpu-memory-utilization 0.82` with `Qwen3-Embedding-8B` resident and idle beside it,
not the chat model alone. The co-tenant costs 91,482 tokens of KV pool; what it costs in
throughput was not isolated.

**The thinking switch was verified first**, as the protocol requires: `enable_thinking:
false` takes `reasoning_tokens` from 93 to 0. See the
[field-name trap](../README.md#the-reasoning-text-is-in-reasoning-not-reasoning_content).

**One run per arm.** The setups compared against here state two- or three-run
spreads; this does not.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **51.9 tok/s** | 45.3 tok/s |
| Total, incl. prompt | 430.8 tok/s | 1084.9 tok/s |
| Requests | 0.30 req/s | **0.85 req/s** |
| Latency p50 | 3.84 s | **1.13 s** |
| Tokens per answer | 173 (**76 %** reasoning) | 53 (0 %) |
| GPU utilisation | 100 % · 100 % | 99 % · 100 % |

## Decode rate, measured separately

`v1` reports output tokens over a 40 s window, which mixes prefill into the figure. A
streaming request measures the two apart: tokens after the first, divided by
`duration − TTFT`.

| | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 | 128 | 0.11 s | **49.6 tok/s** |
| thinking on, run 2 | 272 | 0.10 s | **49.5 tok/s** |
| thinking off, run 1 | 51 | 0.10 s | **49.5 tok/s** |
| thinking off, run 2 | 44 | 0.10 s | **49.5 tok/s** |
| thinking on, 64k prompt | 291 | 10.57 s | **45.7 tok/s** |

**49.5 tok/s in both arms, spread 0.2 % over four runs.** Thinking does not change how
fast a token is produced — it changes how many are produced. The 51.9 against 45.3 in
the `v1` table above is therefore an artefact of the measurement window, not a property
of the model: short answers pay the 1,270-token prompt more often inside 40 s.

**Decode holds up at depth**: 45.7 tok/s with 64,000 tokens of context, 8 % below empty.

## Reading

**Both cards sit at 100 % on a single request.** Dense at BF16 reads all 25.9 GiB of
per-card weights for every token, so one stream already saturates memory bandwidth.
There is no idle capacity at concurrency 1 to be won back by batching harder — what
batching buys here is amortising those same weight reads over more tokens, which is
exactly what the [concurrency ladder](concurrent-load.md) shows.

**Three quarters of a default answer is thinking**, 131 of 173 tokens. The visible reply
is about the same length in both arms (252 against 334 characters in the
[reasoning-cost](reasoning-cost.md) runs); what thinking adds is the scratchpad.

**The two output-tok/s figures are not a decode-rate comparison.** `v1` reports tokens
generated over the 40 s window, so a short answer pays prefill of the pinned ~1,270-token
prompt proportionally more often. Thinking-off produces *fewer* output tokens per second
while producing nearly three times as many answers — the arms differ in answer length,
not in how fast the model emits a token.

## Against DeepSeek-V4-Flash-0731

Same machine, same protocol, [its own file](../../../deepseek-v4-flash-0731/sglang/scenarios/single-stream.md):

| thinking off, concurrency 1 | this setup | DeepSeek-0731 |
|---|---|---|
| Output | 45.3 tok/s | **75.3–75.5 tok/s** |
| Requests | 0.85 req/s | **2.08–2.12 req/s** |
| Latency p50 | 1.13 s | **0.47 s** |
| Tokens per answer | 53 | 35–36 |

**0.60× the tokens per second and 2.4× the latency**, against a model with ten times the
parameters. This is the expected direction and the reason it is worth writing down: a
284 B mixture-of-experts activates a fraction of itself per token, a 27 B dense model
reads all of itself. Parameter count does not predict decode speed; **active** parameter
count does.

The latency gap is wider than the throughput gap because the answers differ in length —
53 tokens against 35. Per token the difference is 2.4× / (53/35) ≈ 1.6×, close to the
0.60× on throughput.
