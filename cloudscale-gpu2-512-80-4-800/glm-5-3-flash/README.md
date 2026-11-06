# GLM-5.3-Flash · NVFP4

Z.ai's GLM-5.3-Flash in NVIDIA's ModelOpt NVFP4 quantisation, on all four cards of
[this machine](../README.md), measured 2026-11-06. First measurement of this model in
this repository.

| | |
|---|---|
| Checkpoint | [`nvidia/GLM-5.3-Flash-NVFP4`](https://huggingface.co/nvidia/GLM-5.3-Flash-NVFP4) — 204.4 GB, ModelOpt 0.47 NVFP4; base [`zai-org/GLM-5.3-Flash`](https://huggingface.co/zai-org/GLM-5.3-Flash) (328 GB FP8) |
| Architecture | `Glm5NextForConditionalGeneration` — 321 B total, 18 B active, hybrid sparse and linear attention, manifold-constrained hyper-connections |
| Setup | [vLLM 0.33.0, TP=4 with expert parallelism, FP8 KV cache](vllm/) |
| Context served | 262,144 (1 M native) |
| Modality | text and images |
| Thinking | **cannot be switched off** — `reasoning_effort` low / high / max, default max |

## Verdict

**The NVFP4 pack runs on these sm120 cards with stock vLLM, although NVIDIA lists only
GB200 as tested.** FP4 GEMMs go through FlashInfer's `CutlassFp4GemmRunner`; nothing had
to be patched or built.

**At its default effort it is the slowest model to answer on this machine**: 376 tokens
per answer, 83 % of them thinking, so 0.28 answers/s alone and 6.4 at 256 clients with a
p50 of 86 s. The token rate is ordinary — 2,347 output tok/s at C=256, level with
Qwen3.8-Flash-Next — but the tokens are scratchpad.

**`reasoning_effort: "low"` is the switch that matters.** It cuts the answer to 52 tokens
with 2–4 % thinking and almost triples the answer rate at C=8 (1.15 → 3.17/s). Neither
`enable_thinking: false` nor `reasoning_effort: "none"` does anything: both are accepted
and still produce 24–31 reasoning tokens, so the protocol's thinking-off arm does not
exist for this model and `low` takes its place in [`q1`](vllm/scenarios/quality.md).

| | GLM-5.3-Flash NVFP4 | MiMo-V2.6-Flash-RL FP8 | Qwen3.8-Flash-Next FP8 |
|---|---|---|---|
| Single stream, default thinking | 103.5 tok/s, p50 3.49 s | 140.2 tok/s, p50 0.48 s | 110.4 tok/s, p50 1.86 s |
| Tokens per answer, default | **376** (83 % thinking) | 68 (21 %) | 210 (78 %) |
| C=256, default thinking | 2,346.7 tok/s · **6.40 answers/s**, p50 86 s | 3,739.6 · 54.98, p50 4.8 s | 2,274.9 · 11.38, p50 26 s |
| Decode | 101–102 tok/s, flat | 143 tok/s | 115 tok/s |
| Prefill 64k / 128k / 250k | **6,353 / 5,301 / 6,360** tok/s | 6,104 / 4,865 / 3,561 | 7,591 / 7,782 / 7,840 |
| Needles at 250k | 3 of 3 | 3 of 3 | 3 of 3 |
| KV pool | 4,291,550 tokens (FP8) | 4,294,730 | 3,613,443 |

**Prefill stays flat to 250k**, unlike MiMo's: the linear-attention layers carry most of
the context, and a full 250,000-token prompt starts answering after 39 s against MiMo's 70.

**Under `q1` it is level with Qwen3.8-Flash-Next at the default effort and buys no lead with
its thinking**: MMLU-Pro 0.870, GSM8K 0.985, HumanEval 0.970, IFEval 0.880 against Qwen's 0.930.
At `low` it keeps arithmetic and code (0.985, 0.939) and gives up 5–7 points on knowledge
and instructions — [quality](vllm/scenarios/quality.md).

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [reasoning cost](vllm/scenarios/reasoning-cost.md) · [long context](vllm/scenarios/long-context.md) · [quality](vllm/scenarios/quality.md) |
