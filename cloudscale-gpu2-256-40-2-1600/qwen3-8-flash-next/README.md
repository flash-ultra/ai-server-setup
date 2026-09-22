# Qwen3.8-Flash-Next

Qwen's preview of the Qwen4 architecture, on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md). First measured 2026-08-31,
reconfigured and re-measured 2026-09-21.

| | |
|---|---|
| Checkpoint | [`unsloth/Qwen3.8-Flash-Next-GGUF`](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF) — **UD-Q6_K_XL** current, UD-Q5_K_XL also measured |
| Base model | [`Qwen/Qwen3.8-Flash-Next`](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) |
| Size on disk | 157.5 GiB (Q6) · 147.4 GiB (Q5) · + 0.84 GiB projector |
| Architecture | `Qwen4ExpForConditionalGeneration`, 48 layers, 512 experts, **10 active** |
| Attention | Gated DeltaNet + Qwen Sparse Attention (QSA), micro-block level |
| Context | 262,144 native, no `rope_scaling` — served as 6 slots × 262,144 |
| Modality | text **and images** — `mmproj-F16.gguf` ships with the GGUF |

## Verdict

**The only model measured here that fits, sees images, and is current.** What that costs
against the production model is smaller than the first round suggested, and it is not a
throughput cost at all.

| | Measured on Q6, six slots |
|---|---|
| Peak under load | 7.47 answers/s · **1,390.3 output tok/s** at concurrency 256 |
| Latency at that point | p50 133.9 s, p95 226.7 s |
| Single stream | 86.6 tok/s output, p50 **2.01 s**, 182 tokens per answer |
| At 8 concurrent | 209.4 output tok/s, p50 **7.8 s** |
| Prefill, 180k tokens | 134.0 s, 1343 tok/s *(measured on Q5)* |
| Needles at 180k | 3 of 3 *(measured on Q5)* |
| **GPU utilisation** | **39–43 % at every level** (45–47 % on configuration A) |
| VRAM | 87,055 / 81,773 MiB of 97,887 — 10.6 / 15.7 GiB free |

**Single user: good. Small teams: workable. Heavy agent load: still not.** p50 is 2.0 s
at one request, 7.8 s at eight and 28.7 s at thirty-two.
[DeepSeek-V4-Flash-0731](../deepseek-v4-flash-0731/) on the same cards sits at 2.9 s at
thirty-two.

### The throughput gap is an answer-length artefact

Against DeepSeek-0731 at concurrency 256, on the same two cards:

| | DSv4-0731 · SGLang | Qwen3.8-Flash-Next · llama.cpp |
|---|---|---|
| Answers/s | 32.58 | 7.47 |
| **Output tok/s** | 1,173.2 | **1,390.3** |
| Tokens per answer | 35 | 186 |
| Latency p50 | 7.96 s | 133.88 s |

**In tokens per second this setup is 18 % ahead, not five times behind.** The 4.4× gap in
answers per second is answer length: the 0731 setup runs with thinking off by default and
replies in 35 tokens, this one writes 186. Requests per second is the wrong column for
comparing these two, and the earlier "factor of five in throughput" reading came from it.

**Latency remains the real difference** — 133.9 s against 7.96 s at 256, a factor of 17.
That one is not an artefact.

## Six slots, not one

The first round served the full 262,144 context in a single slot. Six slots of the same
size fit beside the Q6 weights, and they change the picture below saturation:

| Concurrent | 1 slot | 6 slots | p50, 1 slot | p50, 6 slots |
|---|---|---|---|---|
| 8 | 121.0 tok/s | **209.4** | 14.70 s | **7.77 s** |
| 16 | 163.2 | **264.4** | 33.70 s | **13.10 s** |
| 256 | 1,301.8 | 1,390.3 | 291.82 s | **133.88 s** |

`--parallel` does not raise the ceiling — both configurations flatten near 1,400 output
tok/s — but it halves latency at every level from 8 upward. Details and the slot sweep
are in [concurrent load](llama-cpp/scenarios/concurrent-load.md).

## Q6 costs 2.1 %

6.9 % more weight, 88.5 → 86.6 tok/s single stream, and unchanged GPU utilisation —
45 %·44 % against 46 %·45 %. On a setup
that leaves half the machine idle there is slack to absorb the extra reads, so the higher
bit depth is close to free. See [single stream](llama-cpp/scenarios/single-stream.md).

Whether the extra bit depth changes answer quality was **not** tested. The throughput
argument alone does not justify the re-download; it only says the re-download is cheap.

## The 45 % is the engine, and this model proves it

Only llama.cpp loads this checkpoint on this machine, and llama.cpp
[cannot split across these cards](../README.md#llamacpp-cannot-split-across-these-cards) —
`-sm row` is rejected by the CUDA backend. The cards alternate instead of working
together, and utilisation pins in the low forties at every level of the ladder, in every
slot configuration and at both quantisations.

**Two architecturally unrelated models land on the same number.** GLM-5.3-Flash has 45
layers with denser activation; this one has 10 of 512 experts and micro-block sparse
attention. Same engine, same ceiling. That was a suspicion with one model and is a
finding with two.

Where the engine is not the constraint, this model is the faster of the pair: 1343
against ~530 tok/s prefill, 86.6 against 45 tok/s single-stream output, at a **higher**
bit depth (Q6 against IQ4) and less memory.

## Measurements

| Setup | Scenarios |
|---|---|
| [`llama-cpp/`](llama-cpp/) | [single](llama-cpp/scenarios/single-stream.md) · [concurrent](llama-cpp/scenarios/concurrent-load.md) · [long context](llama-cpp/scenarios/long-context.md) |

## Model-specific gotchas

**A short `max_tokens` returns empty `content`.** Measured on one image question:
`max_tokens` 300 and 2500 both came back with the budget fully consumed and nothing
visible. At 8000 the answer arrived. Every `v1` number here was measured at the pinned
512, so part of what the tables count is truncated thinking rather than finished answers.

**`--image-min-tokens 1024` changes the input but not this answer.** The load log warns
that Qwen-VL needs at least 1024 image tokens for grounding tasks. Setting it raised the
probe image from 288 to 1150 prompt tokens — and the shape answer stayed wrong. Asked to
justify with side lengths and given 8000 tokens, the same model gets it right. The limit
was the thinking budget, not the resolution.

**`-c` is the pool, not the per-slot budget.** Divided by `--parallel` it must stay at or
below 262,144, the checkpoint's `max_position_embeddings`. There is no `rope_scaling`, and
a larger per-slot budget loads without an error.

**Reasoning share reads 0 %.** llama.cpp does not send
`completion_tokens_details.reasoning_tokens`. It means "not reported" — 182 tokens for a
three-sentence summary says otherwise.

## Still open

- **Whether thinking can be switched off.** Not probed; no key verified, so no
  `reasoning` scenario. The Qwen model card documents `enable_thinking`,
  `preserve_thinking` and `reasoning_effort`, but whether llama.cpp forwards them was not
  tested. This is the cheapest remaining experiment and the one with the most upside:
  thinking off would remove most of the answer-length gap against DeepSeek-0731.
- **Quality.** No comparison against the other models on real work, and none between Q5
  and Q6.
- **Long context on six slots.** The 3-of-3 needle result at 180k was measured at one
  slot on Q5.
