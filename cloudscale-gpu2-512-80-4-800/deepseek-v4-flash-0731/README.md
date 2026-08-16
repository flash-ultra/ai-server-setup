# DeepSeek-V4-Flash-0731

Two server setups measured with the same checkpoint on
[cloudscale `GPU2-512-80-4-800`](../README.md) — 4× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 14–15 August 2026.

| | |
|---|---|
| Checkpoint | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) |
| Architecture | `deepseek_v4`, 43 layers, 256 experts (non-REAP), 6 active |
| Parameters | 284.33 B |
| Attention | MLA — 64 query heads, **1 KV head** |
| Native context | 1,048,576 (YaRN, factor 16 from 65,536) |
| Speculation | DSpark (`dspark_block_size: 5` shipped, **use 7** on SM120) |
| MTP | not available on this release — DSpark only |

## Verdict

**Production: [SGLang with SM120 patchset](sglang/).** [llama.cpp](llama-cpp/) remains
configured as a fallback.

| Concurrency | llama.cpp req/s | SGLang req/s | llama.cpp TTFT | SGLang TTFT |
|---|---|---|---|---|
| 1 | 0.42 | 0.62 | 0.05 s | 0.15 s |
| 8 | 1.10 | 2.12 | 0.24 s | 0.18 s |
| 16 | 1.40 | 3.83 | 0.31 s | 0.20 s |
| 32 | 1.73 | **5.55** | **13.71 s** | **0.25 s** |
| 64 | — | 7.95 | — | 0.32 s |

At 32 concurrent requests SGLang serves 3.2× the requests at 55× lower latency,
running all four GPUs at 91–95 % utilisation versus llama.cpp's 20 %.

Peak on the SGLang stack **as shipped**: 27,026 total tok/s at concurrency 256 — a
pre-`v1` figure, so it compares to the numbers below on requests per second but not on
tokens ([why](sglang/scenarios/concurrent-load.md#throughput)). That
sweep was stopped by the configured request limit, not by the throughput curve
flattening — and raising the limit confirmed it: a
[configuration sweep](sglang/scenarios/concurrent-load.md#configuration-sweep-protocol-v1)
reaches **74 % more answers per second** at concurrency 768 with
`--max-running-requests 1024`. The shipped configuration is not the throughput optimum;
it is a latency choice. One neighbouring setting crashes the scheduler outright, so the
faster configuration is a measured finding, not yet a recommendation.

## Server setups

| Setup | Role | Engine | Startup |
|---|---|---|---|
| [`sglang/`](sglang/) | production since 2026-08-15 | SGLang v0.5.16 + SM120 patchset | 151 s warm · 274 s cold |
| [`llama-cpp/`](llama-cpp/) | fallback | llama.cpp `7e4c0a96`, GGUF UD-Q8_K_XL | 20 s warm |

### Scenario coverage

| Scenario | llama.cpp | SGLang |
|---|---|---|
| Single stream | [measured](llama-cpp/scenarios/single-stream.md) | [measured](sglang/scenarios/single-stream.md) |
| Concurrent load | [C 1–32](llama-cpp/scenarios/concurrent-load.md) | [C 1–256 + prompt mix](sglang/scenarios/concurrent-load.md) |
| Long context | [0–128k](llama-cpp/scenarios/long-context.md) | [full 1M verified](sglang/scenarios/long-context.md) |
| Reasoning cost | not measured | [measured](sglang/scenarios/reasoning-cost.md) |

## The one finding that decided it

llama.cpp has **no tensor parallelism for this architecture**:

```
-sm row     → failed to load model
-sm tensor  → failed to load model
-sm layer   → works (the only mode that loads)
```

Both alternatives fail even with a self-built sm120 binary. The cause is
`attention.head_count_kv = 1` — a single KV head cannot be split across four cards.
In layer-split mode the cards work one after another, which caps utilisation at
11–14 % each regardless of load. Four cards at 14 % is roughly one saturated GPU.

SGLang sidesteps this by combining three parallelism axes (tensor, data, expert)
rather than splitting layers.

## Model-specific gotchas

**DSpark draft depth 5 corrupts output on SM120.** That is the value shipped in the
checkpoint's own config. Use 7. The corruption does not show in single tests — only
under varying load across several cold starts.

**96 % of generated tokens are reasoning** with thinking enabled. A trivial question
produced 253 reasoning tokens against 10 tokens of visible answer. Benchmarks that
count only streamed answer text under-report throughput by roughly a factor of 5 —
measure via the `usage` fields.

Two consequences, both measured in [reasoning cost](sglang/scenarios/reasoning-cost.md):
per-request `thinking: false` gives 3.5× the answers per second at an eighth of the
tokens, while `reasoning_effort` changes almost nothing under load. And with thinking
on, reasoning eats the `max_tokens` budget — visible answers came back at 107
characters against 223 with it off, because the answer is truncated after the thinking.

**Sampling is not optional:** `temperature 1.0`, `top_p 1.0`. Lower values drive this
checkpoint into repetition loops. For llama.cpp additionally `min_p 0.01`.

**No MTP.** Earlier Flash releases shipped MTP heads; 0731 does not. Published
benchmarks labelled "MTP on" come from a different checkpoint and are not comparable.

**The checkpoint ships its DSpark configuration:**

```
dspark_block_size: 5          dspark_target_layer_ids: [40, 41, 42]
dspark_markov_rank: 256       num_nextn_predict_layers: 1
```

Note that the shipped block size of 5 is exactly the value that corrupts output on
SM120 — use 7.

## References

- [DeepSeek-V4-Flash-0731](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) — base checkpoint
- [HF discussion #22](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731/discussions/22) — community results on the same GPU configuration

Setup-specific sources are listed in the respective setup README.

## Still open

The questions that would change a decision. Each is owned by the document that would
answer it.

- [DSpark correctness under bursty load](sglang/README.md#still-open) — five cold
  starts, to rule out silent draft corruption with more than a single-run confidence
- [Prefill decay between 128k and 1M](sglang/scenarios/long-context.md#not-measured) —
  only the two endpoints are measured, the curve between them is guessed
- [Prefix-cache benefit on a warm 1M context](sglang/scenarios/long-context.md#not-measured)
  — decides whether the 7:51 min cold prefill is a one-off or a per-query cost
- [Answer quality with thinking off](sglang/scenarios/reasoning-cost.md#not-measured) —
  the 8.75× cost saving is measured, but only length and throughput; whether those
  answers are as good needs a task-specific evaluation
- [Stability of the faster configuration](sglang/scenarios/concurrent-load.md#not-measured)
  — `--max-running-requests 1024` measures 74 % better but sits next to a setting that
  hard-crashes; repeat and sustained-load runs decide whether it can be adopted
- [llama.cpp at full context](llama-cpp/scenarios/long-context.md#not-measured) — the fallback
  is verified only to 128k

Smaller gaps, and the knobs deliberately dropped when the llama.cpp series was cut
short, are listed in the [SGLang](sglang/README.md#still-open) and
[llama.cpp](llama-cpp/README.md#not-planned) setup READMEs.
