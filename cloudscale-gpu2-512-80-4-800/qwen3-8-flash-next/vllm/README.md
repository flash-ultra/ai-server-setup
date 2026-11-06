# vLLM 0.33.0, Docker — Qwen3.8-Flash-Next-FP8 on four cards

The model that the Rocky two-card machine
can only serve as a 3-bit GGUF under Strata, here at the author's FP8 under vLLM with every
expert on the cards. Set up and measured 2026-11-06.

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` (torch 2.14.0+cu130, transformers 5.20.2), `serve-vllm.sh` |
| Checkpoint | [`Qwen/Qwen3.8-Flash-Next-FP8`](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8) — 185.5 GB, fine-grained FP8 e4m3 (block 128) |
| Architecture | `Qwen4ExpForConditionalGeneration` — 125 B total, 6 B active, 48 layers in 12 × (3 × Gated DeltaNet + 1 × Qwen Sparse Attention), 512 experts (10 routed + 1 shared), plus a 51 B n-gram embedding and a 4 B MTP head |
| Cards | 4 of 4 (TP=4) |
| Modality | text, image, video |
| Context served | **262,144** (native; 1 M with YaRN not enabled) |

## Configuration in effect

```
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --trust-remote-code
  --gpu-memory-utilization 0.90 --max-model-len 262144
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder --enable-auto-tool-choice
```

| | this machine |
|---|---|
| Weights + non-torch per card | **34.7 GiB** |
| VRAM per card | 85,299 of 97,887 MiB |
| KV cache per card | **45.9 GiB** |
| KV pool | **3,613,443 tokens** — 13.78 full-length requests at 262,144 |
| Start to ready | **151 s** — weights 20 s, engine init 105 s, graph capture 20 s |
| FP8 MoE backend | Triton (`TRITON Fp8 MoE`); FlashInfer/DeepGEMM not selected on sm120 |
| All-reduce | PyNCCL (custom all-reduce not used; P2P is available on this machine) |

**Ten times the KV pool of the 27B on the Rocky two-card machine (2× RTX PRO 4500)**, and 45 GiB per card to spare
at `0.90`. The engine suggests `--kv-cache-memory` 53.5 GiB to use the rest.

## Pinned values

Verified 2026-11-06 with `smoke.sh`:

| Setting | Value | Verified |
|---|---|---|
| `--reasoning-parser` | `qwen3` | thinking text arrives in `message.reasoning`, `content` holds only the answer |
| `--tool-call-parser` | `qwen3_coder` | weather question with one tool → `finish_reason: tool_calls`, structured `tool_calls` |
| thinking switch | `enable_thinking: false` **or** `reasoning_effort: "none"` | `reasoning_tokens` 44 → 0 under both; thinking is **on by default** |

## Result, in tokens per second

| | this: vLLM FP8 TP=4, 4× RTX PRO 6000 | Rocky 2× RTX PRO 4500: Strata IQ3_S, 2× RTX PRO 4500 |
|---|---|---|
| Output, single stream, thinking on | 110.4 — **175.4 with the MTP draft** | 141.4 |
| Output, single stream, thinking off | 97.9 — **132.4 with the MTP draft** | 108.5 |
| Decode, measured separately | 115 — **163–192 with the MTP draft** | 136–150 |
| Prefill at 64k / 128k | **7591 / 7782** | 5957 / 6348 (120k) |
| Output at C=8 / C=16, thinking on | **446.6 / 654.2** | 346.0 / 391.0 |
| Output at C=256, thinking on | **2274.9** | queue |
| Needles at 250k | **3 of 3** (window 262k) | — (window 131k) |
| Start to ready | **151 s** | 308 s |

**Under load this is a different machine: 2,275 output tok/s at 256 clients and a KV pool
for fourteen full-length conversations.** On the single stream the plain run loses to the
two-card Strata setup, which drafts with the model's MTP head; with
`--speculative-config qwen4_exp_mtp` vLLM drafts too and takes the single stream to
**175 tok/s**, 1.24× Strata on the Rocky two-card machine (2× RTX PRO 4500), at an acceptance length of 2.06. Under
load the draft changes nothing.
The FP8 checkpoint against the 3-bit one: [`q1`](scenarios/quality.md) cannot tell them apart.

## Scenarios

| Scenario | Status |
|---|---|
| [single-stream](scenarios/single-stream.md) | measured — 110.4 output tok/s thinking on, 97.9 off, decode a flat 115; **with the MTP draft 175.4 / 132.4, decode 163–192** |
| [concurrent-load](scenarios/concurrent-load.md) | measured — **2,275 output tok/s at C=256** thinking on, still rising; 18.65 answers/s at C=256 off; mixed traffic at C=32; MTP draft +10–16 % up to C=128, neutral at 256 |
| [reasoning-cost](scenarios/reasoning-cost.md) | measured — thinking costs 2.9× in answers/s, `low` buys a third back |
| [long-context](scenarios/long-context.md) | measured — 64k / 128k / 250k, **3 of 3 needles each**, prefill 7.6–7.8 k tok/s flat |
| [quality](scenarios/quality.md) | measured — `q1`, both arms, **HumanEval 0.976** with thinking (Docker sandbox), IFEval prompt_strict 0.930, GSM8K 0.990, MMLU-Pro 0.885 / 0.860 (2 of 200 truncated); **indistinguishable from the 3-bit Strata run on Rocky 2× RTX PRO 4500** |
