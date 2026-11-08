# DeepSeek-V4-Flash-0731

Three server setups measured with the same checkpoint on
[cloudscale `GPU2-512-80-4-800`](../README.md) — 4× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 14–15 August 2026 with a patched SGLang and llama.cpp, and 7–8 November 2026
with stock vLLM.

| | |
|---|---|
| Checkpoint | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) |
| Architecture | `deepseek_v4`, 43 layers, 256 experts (non-REAP), 6 active |
| Parameters | 284.33 B |
| Attention | MLA — 64 query heads, **1 KV head** |
| Native context | 1,048,576 (YaRN, factor 16 from 65,536) |
| Speculation | DSpark (`dspark_block_size: 5` shipped, **use 7** on SM120) |
| MTP | not available on this release — DSpark only |

## Verdict, November 2026

**Stock vLLM 0.33 replaces the patched stack.** No patches and no draft model, and more
throughput at every load level both were measured at: over the real run time
([why](../../benchmark/README.md#the-window-overstates-slow-answers)) 3,869 tok/s at 256 clients
and 5,956 at 1,024, against 2,762 and 4,438 for the August SGLang patchset read the same way.
With the checkpoint's DSpark module the same image nearly doubles the single stream and falls
behind from 128 clients on.

| Thinking on | [vLLM 0.33](vllm/), no draft | [vLLM 0.33, DSpark](vllm/scenarios/dspark.md) | [SGLang patchset](sglang/), August |
|---|---|---|---|
| Single stream | 95.3 tok/s | **169.8** | 131.2 ¹ |
| C=256, over the real run time | **3,869 tok/s** · 18.8 answers/s | 1,594 · 7.9 | 2,762 · 8.3 |
| C=1024, over the real run time | **5,956 tok/s** · 29.5 answers/s | — | 4,438 · 14.3 |
| Decode | 92 tok/s, 89 behind 64k | 155–320, 183 behind 64k | — |
| Prefill at 250k | 5,844 tok/s, 3/3 needles | — | 1M verified ¹ |
| Context served | 262,144 | 262,144 | 1,048,576 |
| `q1` MMLU-Pro / IFEval / HumanEval | 0.870 / 0.925 / 0.970 | — | — |

¹ measured before protocol `v1`.

**Without thinking four cards give what two gave with the patched SGLang:** 29.8–31.5 answers/s from 256 to
768 clients, against 32.1–33.4 for the patched SGLang on the
[two-card machine](../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-flash-0731/). The 37-token
answers leave prefill as the limit. Four data-parallel copies, which would have quadrupled the
cache, [do not start](vllm/README.md#what-did-not-run) on this vLLM.

## Verdict, August 2026

**Production: [SGLang with SM120 patchset](sglang/).** [llama.cpp](llama-cpp/) was the
alternative it was measured against; it is no longer deployed and its weights were
removed from the machine on 2026-08-16.

| Concurrency | llama.cpp req/s | SGLang req/s | llama.cpp TTFT | SGLang TTFT |
|---|---|---|---|---|
| 1 | 0.42 | 0.62 | 0.05 s | 0.15 s |
| 8 | 1.10 | 2.12 | 0.24 s | 0.18 s |
| 16 | 1.40 | 3.83 | 0.31 s | 0.20 s |
| 32 | 1.73 | **5.55** | **13.71 s** | **0.25 s** |
| 64 | — | 7.95 | — | 0.32 s |

At 32 concurrent requests SGLang serves 3.2× the requests at 55× lower latency,
running all four GPUs at 91–95 % utilisation versus llama.cpp's 20 %.

Peak on the SGLang stack **as shipped**: 11.12 req/s at concurrency 256, 8.2 over the real
run time ([why](../../benchmark/README.md#the-window-overstates-slow-answers)) — a pre-`v1`
figure, so it compares to the numbers below on requests per second but not on tokens
([why](sglang/scenarios/concurrent-load.md#throughput)). That
sweep was stopped by the configured request limit, not by the throughput curve
flattening — and raising the limit confirmed it: a
[configuration sweep](sglang/scenarios/concurrent-load.md#configuration-sweep-protocol-v1)
reaches **71 % more answers per second** at concurrency 1024 with
`--max-running-requests 1024`, over the real run time. The shipped configuration is not the throughput optimum;
it is a latency choice. One neighbouring setting crashes the scheduler outright, so the
faster configuration is a measured finding, not yet a recommendation.

## Server setups

| Setup | Role | Engine | Startup |
|---|---|---|---|
| [`vllm/`](vllm/) | measured 2026-11-07/08 | vLLM 0.33.0, unpatched, TP=4 + EP | 522 s, 572 s with DSpark |
| [`sglang/`](sglang/) | production since 2026-08-15 | SGLang v0.5.16 + SM120 patchset | 151 s warm · 274 s cold |
| [`llama-cpp/`](llama-cpp/) | measured, not deployed | llama.cpp `7e4c0a96`, GGUF UD-Q8_K_XL | 20 s warm |

### Scenario coverage

| Scenario | llama.cpp | SGLang | vLLM 0.33 |
|---|---|---|---|
| Single stream | [measured](llama-cpp/scenarios/single-stream.md) | [measured](sglang/scenarios/single-stream.md) | [measured](vllm/scenarios/single-stream.md) |
| Concurrent load | [C 1–32](llama-cpp/scenarios/concurrent-load.md) | [C 1–256 + prompt mix](sglang/scenarios/concurrent-load.md) | [C 1–1024 + prompt mix](vllm/scenarios/concurrent-load.md) |
| Long context | [0–128k](llama-cpp/scenarios/long-context.md) | [full 1M verified](sglang/scenarios/long-context.md) | [to 250k](vllm/scenarios/long-context.md) |
| Reasoning cost | not measured | [measured](sglang/scenarios/reasoning-cost.md) | [measured](vllm/scenarios/reasoning-cost.md) |
| Quality (`q1`) | not measured | not measured | [both arms](vllm/scenarios/quality.md) |
| DSpark | — | in the production config | [measured separately](vllm/scenarios/dspark.md) |

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
