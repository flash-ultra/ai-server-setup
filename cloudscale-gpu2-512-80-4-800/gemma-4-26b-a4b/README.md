# Gemma-4-26B-A4B

Sparse Gemma-4, 26 B total with 4 B active, measured on a single RTX PRO 6000 under
three engines. Tested 2026-08-16.

| | |
|---|---|
| Checkpoint | [`google/gemma-4-26B-A4B-it`](https://huggingface.co/google/gemma-4-26B-A4B-it) |
| Weights used | `unsloth/gemma-4-26B-A4B-it-GGUF` BF16 (llama.cpp) · `unsloth/gemma-4-26B-A4B-it` safetensors (SGLang, vLLM) |
| Architecture | `gemma4`, MoE, 4 B active per token |
| Context | 256 K native; measured at 32,768 |
| Speculation | MTP shipped as `gemma4-assistant` |
| Modality | text + vision; only text measured |

## Verdict

**vLLM for load, any of the three for a single user.** At concurrency 32 vLLM serves
31.88 answers per second against SGLang's 21.55 and llama.cpp's 5.45 — with *better*
latency, not worse. At concurrency 1 the three are within 14 % of each other. The whole
difference is batching; see [engine comparison](engine-comparison.md).

**And prefer this model over the dense Gemma-4-31B on one card.** Same engine, same
configuration, same card: 2.6× the output tokens at concurrency 32 and 3.9× better
median latency, at a comparable parameter count.

## Measurements

| Setup | Scenarios |
|---|---|
| [`llama-cpp/`](llama-cpp/) | [single](llama-cpp/scenarios/single-stream.md) · [concurrent](llama-cpp/scenarios/concurrent-load.md) · [reasoning](llama-cpp/scenarios/reasoning-cost.md) |
| SGLang, vLLM | measured only for the [engine comparison](engine-comparison.md) — no separate setup directory, because nothing was tuned |

## Model-specific gotchas

**The thinking switch is `enable_thinking`.** The protocol default `thinking` — what
DeepSeek-V4 uses — is accepted by the server and silently does nothing. `reasoning_effort`
is also inert here, though it is the control that works on
[Muse Glimmer](../muse-glimmer-30b/llama-cpp/scenarios/reasoning-cost.md).

**With thinking on, `max_tokens` 512 does not leave room for an answer.** At concurrency
32 the model spends 511 tokens and emits **11 characters**. Turning thinking off gives
2.6× the answers per second *and* a 25× longer visible answer — both improve, because the
budget stops being consumed by the trace.

**Engine defaults for thinking differ.** SGLang served this checkpoint with thinking off,
llama.cpp with `--jinja` served it on. Any cross-engine number has to pin the state; see
[the comparison that nearly got published](engine-comparison.md#the-comparison-that-nearly-got-published).

**llama.cpp reports no `reasoning_tokens`.** The reasoning-share column reads 0 % in every
llama.cpp table here and means "not reported", never "did not think".

## Still open

- [Answer quality with thinking off](llama-cpp/scenarios/reasoning-cost.md#not-measured) —
  the 2.6× is throughput; whether the answers hold up needs a task-specific evaluation
- [A stock SGLang build](engine-comparison.md#not-measured) — the image used carries 33
  DeepSeek-V4 patches, and its share of the gap to vLLM is unknown
- [Concurrency above 32](engine-comparison.md#not-measured) — vLLM had not flattened
- Vision. The checkpoint is multimodal, `bench.py` is text-only, and the `mmproj` weights
  were deliberately not downloaded

### Not planned

- **Tuning llama.cpp further for this model.** The engine comparison shows the gap is
  structural rather than a slot-count question; effort belongs on vLLM instead
- **Quantised variants.** BF16 fits one card with 42 GB to spare, so there is nothing to
  buy with a quant here
