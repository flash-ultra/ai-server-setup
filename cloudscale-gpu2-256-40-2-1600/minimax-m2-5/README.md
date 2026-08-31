# MiniMax-M2.5-NVFP4

NVIDIA's quantisation of MiniMax-M2.5, served on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-08-30.

| | |
|---|---|
| Checkpoint | [`nvidia/MiniMax-M2.5-NVFP4`](https://huggingface.co/nvidia/MiniMax-M2.5-NVFP4) |
| Base model | [`MiniMaxAI/MiniMax-M2.5`](https://huggingface.co/MiniMaxAI/MiniMax-M2.5) |
| Size on disk | 130.3 GiB (139.9 GB) |
| Parameters | 116,349,510,656 total, 8 of 256 experts active |
| Architecture | `MiniMaxM2ForCausalLM`, 62 layers, hidden size 3072 |
| Quantisation | NVFP4, `quant_method: modelopt` |
| Native context | 196,608 — served in full |
| Modality | text only, no vision tower |
| Speculation | none configured; vLLM registers `Eagle3MiniMaxM2ForCausalLM`, untested here |

## Verdict

**The fastest thing measured on this machine, and the only large model here that runs on
an unpatched engine.** One setup, [vLLM 0.28.0 at TP=2](vllm/), no fork, no kernel
patchset, no community image.

| | Measured |
|---|---|
| Single stream | 122.4 tok/s visible, 715.7 tok/s total, p50 1.96 s |
| Peak under load | **9.65–9.75 answers/s at concurrency 256** (2947–3126 output tok/s), two runs |
| Prefill, 180k tokens | 69.8 s, 2580 tok/s |
| GPU utilisation | **100 % on both cards at every level** |

The ladder is monotone from concurrency 1 to 256 in **both** runs — no dip, unlike the
[NVFP4 DeepSeek run on the older machine](../../cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/README.md).
Both cards sit at 100 % throughout, which is what distinguishes this from every
llama.cpp path on this hardware. Run-to-run spread is at most 17 % and only 1 % at the
peak, against 74 % at one level on the older stack — so the headline number is a range
that reproduces, not a single lucky window.

**What is not measured: whether it is any good.** Every number here is throughput. The
model card claims 80.2 % on SWE-Bench Verified and 76.3 % on BrowseComp; none of that was
reproduced, and no quality comparison against DeepSeek-V4-Flash or Qwen3.5-122B was run.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [long context](vllm/scenarios/long-context.md) |

## Model-specific gotchas

**Thinking cannot be switched off.** The protocol requires verifying the key before
running the `reasoning` scenario, because an unknown key is accepted and silently
ignored. All four candidates were tried against the same question:

| Request | `reasoning_tokens` |
|---|---|
| no switch | 174 |
| `chat_template_kwargs: {thinking: false}` | 141 |
| `chat_template_kwargs: {enable_thinking: false}` | 181 |
| `reasoning_effort: none` | 202 |
| `reasoning_effort: low` | 162 |

That is noise around one value, not a switch. **The `reasoning` scenario is therefore not
measured** — running it would have produced a table reading "disabling thinking changes
nothing", which is a false negative rather than a result.

**Where the thinking ends up depends on the path, not on the model.** Same question, same
server, two clients:

| Path | `reasoning_tokens` | `len(reasoning_content)` | `len(content)` |
|---|---|---|---|
| direct to vLLM `:8000` | 449 | **0** | 439 |
| through litellm `:4000` | 945 | **3687** | 288 |

Talking to the engine directly puts the whole scratchpad **into `content`**; the gateway
splits it out and leaves a clean answer. A client on the direct path therefore sees a
rambling, preamble-heavy reply and a client on the gateway sees three tidy bullets — from
the same model on the same request. Judge answer quality on the gateway path, or the
model looks far worse than it is. Do not read an empty `reasoning_content` as "did not
think".

**Context is 196,608, not 262,144.** `max_position_embeddings` of the checkpoint. A
gateway that advertises more will produce `ContextWindowExceededError` mid-session.

## Still open

- **No quality measurement.** The reason the model was tried at all.
- **Eagle3 speculative decoding untested.** vLLM registers the architecture; whether a
  draft checkpoint exists for M2.5 was not checked.
