# Muse-Glimmer-30B

Meta's dense 30 B vision model on a single RTX PRO 6000 under llama.cpp.
Tested 2026-08-16.

| | |
|---|---|
| Checkpoint | [`meta-models/Muse-Glimmer-30B`](https://huggingface.co/meta-models/Muse-Glimmer-30B) |
| Weights used | `unsloth/Muse-Glimmer-30B-GGUF` BF16 — 27.8 + 24.1 GB |
| Architecture | `muse-glimmer`, dense |
| Context | 131 K default, 262 K max; measured at 32,768 |
| Speculation | none — no MTP file in the GGUF package |
| VRAM | 53,019 MiB of 97,887 |
| Licence | Apache 2.0 |

## Verdict

**The slowest of the three single-card models for one user, and the most robust under
load.** 28.6 output tokens per second at concurrency 1 against 190.1 for
[Gemma-4-26B-A4B](../gemma-4-26b-a4b/) — but the ordering reverses nowhere: at
concurrency 32 it reaches 520.5 against the sparse Gemma's 816.9. It stays behind
throughout while holding the card at 92–99 %.

That utilisation is what makes this model useful in this directory: it is the control
that showed llama.cpp's idle time on the Gemma runs is not a hardware limit.

## Measurements

| Setup | Scenarios |
|---|---|
| [`llama-cpp/`](llama-cpp/) | [single](llama-cpp/scenarios/single-stream.md) · [concurrent](llama-cpp/scenarios/concurrent-load.md) · [reasoning](llama-cpp/scenarios/reasoning-cost.md) |

## Model-specific gotchas

**The chat template contains no thinking switch.** Neither `thinking` nor
`enable_thinking` appears in it, and both are accepted and ignored — the
[reasoning scenario](llama-cpp/scenarios/reasoning-cost.md) keeps the inert row in the
table so the absence is measured rather than asserted.

**`reasoning_effort=low` is the control that works.** Tokens per answer fall from 410 to
140, answers per second rise from 1.27 to 2.23, and the visible answer gets *longer*.
This is exactly reversed from the Gemma-4 checkpoints, where the template switch works
and `reasoning_effort` is inert.

**No speculative decoding.** `meta-models/Muse-Glimmer-30B-assistant` exists as a draft
checkpoint but is not part of the GGUF package used here.

## Still open

- [Speculation](llama-cpp/scenarios/concurrent-load.md#not-measured) — the draft
  checkpoint exists and was never converted or tried
- [`reasoning_effort` beyond `low`](llama-cpp/scenarios/reasoning-cost.md#not-measured)
- Whether the missing template switch is an omission in this GGUF conversion or upstream

### Not planned

- **Vision.** The model is multimodal and `bench.py` is text-only; the `mmproj` weights
  were deliberately left undownloaded
- **SGLang and vLLM.** Neither engine version on this machine knows the `muse-glimmer`
  architecture — llama.cpp is currently the only option, which is itself the finding
