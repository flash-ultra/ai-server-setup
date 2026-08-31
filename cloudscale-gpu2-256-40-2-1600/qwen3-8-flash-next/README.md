# Qwen3.8-Flash-Next

Qwen's preview of the Qwen4 architecture, on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md). Tested 2026-08-31.

| | |
|---|---|
| Checkpoint | [`unsloth/Qwen3.8-Flash-Next-GGUF`](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF) UD-Q5_K_XL |
| Base model | [`Qwen/Qwen3.8-Flash-Next`](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) |
| Size on disk | 147.4 GiB + 0.84 GiB projector |
| Architecture | `Qwen4ExpForConditionalGeneration`, 48 layers, 512 experts, **10 active** |
| Attention | Gated DeltaNet + Qwen Sparse Attention (QSA), micro-block level |
| Context | 262,144 |
| Modality | text **and images** — `mmproj-F16.gguf` ships with the GGUF |

## Verdict

**The only model measured here that fits, sees images, and is current — and it costs a
factor of five in throughput to get that.**

| | Measured |
|---|---|
| Peak under load | 6.83–6.85 answers/s at concurrency 256, two runs |
| Latency at that point | p50 **291.8 s**, p95 548 s |
| Single stream | 88.5 tok/s output, p50 **2.22 s**, 197 tokens/answer |
| Prefill, 180k tokens | 134.0 s, 1343 tok/s |
| Needles at 180k | 3 of 3 |
| **GPU utilisation** | **45 % · 45 % at every level** |
| Run-to-run spread | ≤ 2 % |

**Single user: usable. Agent load: not.** p50 is 2.2 s at concurrency 1 and 58 s at
concurrency 32. [DeepSeek-V4-Flash-0731](../deepseek-v4-flash-0731/) on the same cards
sits at 2.9 s there.

## The 45 % is the engine, and this model proves it

Only llama.cpp loads this checkpoint on this machine, and llama.cpp
[cannot split across these cards](../README.md#llamacpp-cannot-split-across-these-cards) —
`-sm row` is rejected by the CUDA backend. The cards alternate instead of working
together, and utilisation pins at 45 % on every level of the ladder.

**Two architecturally unrelated models now land on the same number.** GLM-5.3-Flash has 45
layers with denser activation; this one has 10 of 512 experts and micro-block sparse
attention. Same engine, same ceiling. That was a suspicion with one model and is a finding
with two.

Where the engine is not the constraint, this model is the faster of the pair: 1343 against
~530 tok/s prefill, 88.5 against 45 tok/s single-stream output, at a **higher** bit depth
(Q5 against IQ4) and 30 % less memory (60/55 GB against 85/81).

## Measurements

| Setup | Scenarios |
|---|---|
| [`llama-cpp/`](llama-cpp/) | [single](llama-cpp/scenarios/single-stream.md) · [concurrent](llama-cpp/scenarios/concurrent-load.md) · [long context](llama-cpp/scenarios/long-context.md) |

## Model-specific gotchas

**A short `max_tokens` returns empty `content`.** Measured on one image question:
`max_tokens` 300 and 2500 both came back with the budget fully consumed and nothing
visible. At 8000 the answer arrived. Every `v1` number here was measured at the pinned 512,
so part of what the tables count is truncated thinking rather than finished answers.

**`--image-min-tokens 1024` changes the input but not this answer.** The load log warns
that Qwen-VL needs at least 1024 image tokens for grounding tasks. Setting it raised the
probe image from 288 to 1150 prompt tokens — and the shape answer stayed wrong. Asked to
justify with side lengths and given 8000 tokens, the same model gets it right. The limit
was the thinking budget, not the resolution.

**Reasoning share reads 0 %.** llama.cpp does not send
`completion_tokens_details.reasoning_tokens`. It means "not reported" — 197 tokens for a
three-sentence summary says otherwise.

## Still open

- **Whether thinking can be switched off.** Not probed; no key verified, so no
  `reasoning` scenario. GLM and MiniMax both had none that worked.
- **Q6_K_XL.** 78.8 GiB per card would fit — 40 GB per card sat unused at Q5.
- **Quality.** No comparison against the other models on real work.
