# Beam-1.0-501B-A23B · NVFP4

Reflection's Beam-1.0 on all four cards of [this machine](../README.md), measured 2026-11-07.

| | |
|---|---|
| Checkpoint | [`reflection/Beam-1.0-501B-A23B-NVFP4`](https://huggingface.co/reflection/Beam-1.0-501B-A23B-NVFP4) — 294 GB, ModelOpt NVFP4; the card puts it within 0.2–1.3 points of BF16 on its own benchmarks |
| Architecture | `BeamForCausalLM` — 501 B total, 23 B active, 256 experts, 52 layers (3 dense), gated GQA with sliding-window attention |
| Setup | [vLLM 0.33.0, TP=4, FP8 KV](vllm/) |
| Context served | 262,144 (1 M native) |
| Modality | text |
| Thinking | **always on**; `reasoning_effort` minimal / low / medium / high / xhigh / max sets a budget hint (8–512), default max |

## Verdict

**The second-highest load throughput on this machine, from the second-largest model.** 3,472
output tok/s and 14.9 answers per second at 256 clients, behind only MiMo (3,740); per
answer it thinks for 247 tokens, a fifth of them visible. One client gets 98 tok/s, and
decode does not move with context.

| Thinking on (default) | Beam-1.0 NVFP4 | DeepSeek-V4.1 EXL3 | MiMo-V2.6-Flash FP8 | GLM-5.3-Flash NVFP4 |
|---|---|---|---|---|
| Single stream | 98.2 tok/s | **153.2** | 140.2 | 103.5 |
| C=256 | **3,472 tok/s · 14.9 answers/s** | 2,112 · 12.9 | 3,740 · 55.0 | 2,347 · 6.4 |
| Tokens per answer | 247 | 170 | 68 | 376 |
| Prefill 250k | 4,616 tok/s | **13,264** | 3,561 | 6,360 |
| KV pool | 2,123,633 tokens | 4,538,321 | 4,294,730 | 4,291,550 |

**The effort switch barely moves it.** `reasoning_effort: low` writes 234 tokens instead of
247 on the protocol prompt, and neither `enable_thinking: false` nor `reasoning_effort:
"none"` exists for this model (`none` is rejected by the chat template). The template maps the
named levels to a budget the model is told about; on a summary prompt it does not keep to it.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [reasoning cost](vllm/scenarios/reasoning-cost.md) · [long context](vllm/scenarios/long-context.md) |
