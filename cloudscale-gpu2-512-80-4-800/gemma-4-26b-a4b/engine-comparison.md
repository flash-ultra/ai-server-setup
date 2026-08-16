# Engine comparison: llama.cpp vs SGLang vs vLLM

One model, one card, one workload — the comparison the DeepSeek-V4 series could not make.

**Model:** Gemma-4-26B-A4B-it · **Machine:** [cloudscale `GPU2-512-80-4-800`](../README.md) ·
measured 2026-08-16

## Why this comparison and not the earlier one

The [DeepSeek-V4 verdict](../deepseek-v4-flash-0731/README.md) put SGLang far ahead of
llama.cpp, but that margin was decided before either engine's scheduler mattered:
DeepSeek-V4 uses MLA with a single KV head, llama.cpp could only layer-split, and four
cards therefore worked one after another. It was a comparison of parallelism strategies.

A model that fits one card removes that variable. Nothing is split, every engine sees the
same weights on the same GPU, and what is left is how each one batches.

## Method

Protocol `v1` — prompt verbatim, `max_tokens` 512, 40 s per level, 3 discarded warmups,
counts from `usage`. Deviations, both recorded in every output header:

- **`--levels 1,4,8,16,32`** — llama.cpp was configured with 16 slots, so 32 is the level
  that shows queueing rather than parallelism
- **`--chat-template-kwargs {"enable_thinking": false}`** — see
  [the trap below](#the-comparison-that-nearly-got-published)

One engine at a time; the other two containers were stopped, and the remaining three
cards were idle. Each engine was configured for a 32,768-token context and roughly 32
concurrent requests, using its own idiom: `-c 32768 -np 16` for llama.cpp,
`--context-length 32768 --max-running-requests 32` for SGLang,
`--max-model-len 32768 --max-num-seqs 32` for vLLM.

## Single stream

| Engine | Output tok/s | Latency p50 | Tokens/answer |
|---|---|---|---|
| **vLLM** | **139.2** | **0.32 s** | 46 |
| llama.cpp | 135.5 | 0.33 s | 46 |
| SGLang | 122.0 | 0.38 s | 46 |

**For one user at a time the three engines are equivalent** — 14 % between best and
worst, and identical tokens per answer confirms they are doing the same work. Whatever
separates them is not in the forward pass.

## Under load

Answers per second, GPU utilisation in brackets:

| Concurrent | vLLM | SGLang | llama.cpp |
|---|---|---|---|
| 1 | 3.08 (98 %) | 2.67 (93 %) | 2.98 (73 %) |
| 4 | 7.78 (100 %) | 6.40 (88 %) | 4.17 (47 %) |
| 8 | 12.70 (100 %) | 9.90 (83 %) | 4.35 (36 %) |
| 16 | 19.98 (100 %) | 14.65 (83 %) | 4.38 (32 %) |
| 32 | **31.88 (100 %)** | 21.55 (76 %) | 5.45 (38 %) |

Median latency at the same levels:

| Concurrent | vLLM | SGLang | llama.cpp |
|---|---|---|---|
| 1 | 0.33 s | 0.38 s | 0.34 s |
| 8 | 0.64 s | 0.83 s | 1.81 s |
| 32 | **1.03 s** | 1.56 s | **6.48 s** |

## Reading

**vLLM delivers 5.9× the answers per second of llama.cpp at concurrency 32 — and does it
with better latency, not worse.** 1.03 s against 6.48 s. This is not a throughput-latency
trade; one engine is simply better at this workload on both axes at once.

**llama.cpp stops scaling after 4 concurrent requests.** 4.17 → 4.35 → 4.38 answers per
second across 4, 8 and 16 — flat — while vLLM goes 7.78 → 12.70 → 19.98 on the same card.
The extra load queues instead of batching.

**GPU utilisation tells the story directly.** vLLM holds 98–100 % at every level. SGLang
sits at 76–93 %. llama.cpp falls to 32 %. Same model, same weights, same card: the idle
time is the scheduler, and nothing else is left to blame.

> **Two earlier explanations for that idle time were wrong, and this run is what settled
> it.** Speculative decoding was the first guess — refuted by
> [a control run with MTP disabled](llama-cpp/README.md#mtp-helps-throughput-and-does-not-explain-the-utilisation-curve),
> which loses utilisation just as fast. Compute-per-token was the second, on the grounds
> that a 4 B-active model cannot fill a card — refuted here, because vLLM fills it to
> 100 % with exactly that model. What remains is llama.cpp's batching, and the dense
> [Muse Glimmer](../muse-glimmer-30b/llama-cpp/scenarios/concurrent-load.md) holding
> 92 % on llama.cpp is consistent with it: a model heavy enough per token hides the gaps
> the scheduler leaves.

**SGLang sits between the two and closer to vLLM.** 21.55 against 31.88 answers per
second, and its utilisation drifts down under load where vLLM's does not. The version
here is the DeepSeek-V4 fork carrying 33 patches, not a stock build, which is a plausible
part of the gap and was not isolated.

## The comparison that nearly got published

The first attempt produced this, before anything was pinned:

| Engine | Answers/s | Tokens/answer |
|---|---|---|
| SGLang | 2.70 | **45** |
| llama.cpp | 0.38 | **506** |

A factor of seven — and entirely an artefact. **SGLang served this checkpoint with
thinking off by default; llama.cpp with `--jinja` served it with thinking on.** Both were
correctly configured; they simply read the same chat template differently. The
throughput difference was the trace, not the engine.

`bench.py` now carries `--chat-template-kwargs`, which applies to every request and is
written into the output header, so the state is pinned rather than inherited. The rule
generalises: **anything an engine defaults to is a variable in a cross-engine comparison
until it is set explicitly.**

## Not measured

- A stock SGLang build. The image here is the DSv4 fork with 33 patches; how much of the
  gap to vLLM belongs to the fork is unknown
- Concurrency above 32, where vLLM had not flattened and llama.cpp had long since
- The same comparison with thinking on. Every number here is thinking-off; the
  [model's own scenarios](llama-cpp/scenarios/concurrent-load.md) cover thinking-on but
  only on llama.cpp
- Whether more slots would move llama.cpp's stall point. 16 slots was chosen to fit one
  configuration across three models, and `-c` ÷ `-np` had to stay above the prompt length
