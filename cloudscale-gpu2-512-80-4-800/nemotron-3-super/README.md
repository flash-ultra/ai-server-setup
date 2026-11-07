# NVIDIA Nemotron-3-Super-120B-A12B · NVFP4

NVIDIA's mid-size hybrid on [this machine](../README.md), measured 2026-11-07. Small enough
for one card, so it runs as **four copies, one per card**, behind one endpoint.

| | |
|---|---|
| Checkpoint | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4) — 80 GB, ModelOpt NVFP4 |
| Architecture | `NemotronHForCausalLM` — 120 B total, 12 B active; Mamba-2 + Transformer hybrid with latent mixture-of-experts and an MTP head |
| Setup | [vLLM 0.33.0, `--data-parallel-size 4`, TP=1](vllm/) |
| Context served | 262,144 per request (1 M native) |
| KV pool | **10,680,687 tokens per copy**, 40.7 full-length requests per card |
| Thinking | on by default; off with `chat_template_kwargs: {enable_thinking: false}`; `reasoning_effort` is ignored |

## Verdict

**A long-context workhorse rather than a speed record.** Each copy decodes a flat 87 tok/s,
whether the answer is 70 tokens or 1,500 and whether 64k of context sits in front of it;
one card reads a 128k prompt at 8,000 tok/s; the Mamba layers keep 10.7 M tokens of cache
per card. Four copies reach 2,408 tok/s at 256 clients over the real run time — above
Qwen3.8-Flash-Next under vLLM, below MiMo — but a single answer is the slowest on this machine.

| Thinking on | Nemotron-3-Super, DP=4 | Qwen3.8-Flash-Next FP8, TP=4 | MiMo-V2.6-Flash FP8, TP=4 |
|---|---|---|---|
| Single stream | 83.1 tok/s | 110.4 | 140.2 |
| Decode | 87 tok/s, flat | 115 | 143 |
| C=256, over the real run time | 2,408 tok/s · 13.9 answers/s | 1,989 · 9.9 | 3,650 · 53.7 |
| Prefill 128k | 8,043 tok/s **on one card** | 7,782 on four | 4,865 on four |
| Needles at 250k | 3 of 3 | 3 of 3 | 3 of 3 |

**Under `q1` it holds its own**: GSM8K 0.970, IFEval 0.910, HumanEval 0.982 with thinking —
level with Qwen3.8-Flash-Next — and MMLU-Pro 0.830, three points behind. With thinking off it
keeps reasoning in the visible answer, and some answers loop until the token cap
([quality](vllm/scenarios/quality.md)).

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [reasoning cost](vllm/scenarios/reasoning-cost.md) · [long context](vllm/scenarios/long-context.md) · [quality](vllm/scenarios/quality.md) |
