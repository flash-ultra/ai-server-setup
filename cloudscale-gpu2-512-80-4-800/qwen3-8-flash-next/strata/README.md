# Strata 0.2.11 — Qwen3.8-Flash-Next on four cards, IQ3_S and Q8_0

The engine that carries this model on the two 32 GB cards of
the Rocky two-card machine, here with
382 GiB of VRAM: every expert resident on the first start, two packs — the 3-bit GSQ-RCO
that the small machine runs, and unsloth's Q8_0 as the reference precision — and the
[vLLM FP8 run](../vllm/README.md) on the same cards as the engine-to-engine comparison.
Set up and measured 2026-11-06.

| | |
|---|---|
| Engine | [`Niko1221/Strata`](https://github.com/Niko1221/Strata) v0.2.11 (release 2026-11-05); the engine binary is the **prebuilt 0.1.57 `linux-x86_64-cuda-cuda13`** from the project's update feed (sm_120 + compute_120), not a local build — `strata-setup.sh` |
| Packs | [`ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) **IQ3_S** (54.8 + 28.8 GB) · [`unsloth/Qwen3.8-Flash-Next-GGUF`](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF) **Q8_0** (188 GB, 6 shards, converted by `setup.sh` into the engine's form: 460 tensors, max error 0.0144) |
| Draft | the model's MTP layer, `--mtp` (5.2 GB download, prepared per pack) |
| Cards | 4 of 4, **layer split** 0–11 / 12–23 / 24–35 / 36–47, one hand-off per verify window |
| Modality | text and images (vision encoder on the GPU) |
| Context served | 262,144, KV int8, 32,768 tokens of KV resident in VRAM, n-gram table in RAM (`--ple-io ram`) |
| API | OpenAI-compatible on port 8080, model name `qwen3.8-flash-next-iq3_s` / `…-q8_0`; thinking off via `reasoning_effort: "none"` or `enable_thinking: false` (verified: 50 → 4 completion tokens); `usage` carries **no** `reasoning_tokens`, so the reasoning share reads 0 % in every table below — not reported, not absent |

## Configuration in effect, IQ3_S

Written by `setup.sh --yes --family qwen --model IQ3_S --gpus all --vision gpu --context 262144`:

```
strata --pack …/packs/iq3_s --native …/IQ3_S/…-00001-of-00002.gguf --ple-gguf …/…-00002-of-00002.gguf
  --expert-profile data/expert-profile.bin --expert-cache auto --prefill auto
  --spec 4 --spec-min-p 0.5 --mtp …/mtp/rt
  --max-context 262144 --kv int8 --ple-io ram --kv-resident 32768 --vision --vram-reserve-mib 700
server.py --engine strata --config strata-iq3_s.json --port 8080 --parallel 8
```

| | |
|---|---|
| VRAM per card with everything loaded | 23.5 / 22.9 / 23.8 / 25.7 GB of 97.9 — **72–74 GB free per card** |
| Host RAM | 121 GB used, 436 GB in cache |
| Experts | **100 % resident** — `the caches hold 24576 of 24576 profiled pairs`, 46.84 GiB loaded at 15.56 GiB/s in 54 s |
| Layer split | `auto`: K = 12, 24, 36 — predicted 8.1 ms per decode window, best of 15 candidates |
| Start to ready | **≈ 60 s** (experts 54 s, page cache warm) |
| Slots | 8 (`--parallel 8`, the engine's maximum) |

## Result, in tokens per second (IQ3_S)

| | Strata IQ3_S, 4 cards | vLLM FP8 TP=4 (+ MTP draft) | Strata IQ3_S, Rocky 2× RTX PRO 4500 |
|---|---|---|---|
| Output, single stream, thinking on | **225.3** | 110.4 (175.4) | 141.4 |
| Output, single stream, thinking off | **140.2** | 97.9 (132.4) | 108.5 |
| Decode, measured separately | **222–254** | 115 (163–192) | 136–150 |
| Prefill at 64k / 128k / 250k | **16,967 / 20,639 / 21,873** | 7,591 / 7,782 / 7,840 | 5,957 / 6,348 (120k) |
| Output at C=8, thinking on | **645.5** | 446.6 (517.3) | 346.0 |
| Output at C=16, thinking on | 722.1 | 654.2 (722.0) | 391.0 |
| Output at C=256, thinking on | queue (8 slots) | **2,274.9** | queue |
| GPU utilisation, single stream | 20–34 % | 99 % | 100 % |
| Start to ready | **≈ 60 s** | 151 s | 308 s |

**The fastest single stream and the fastest prefill in either repository, with the cards
mostly idle.** 225 tok/s and 21,900 tok/s of prefill at 20–34 % and 68–83 % utilisation:
Strata is bounded by its own pipeline here, not by the GPUs, and the same pack gains 1.6×
over the two 32 GB cards of the Rocky two-card machine. Up to eight clients it beats vLLM on the same
hardware; from sixteen on, vLLM's batch takes over, and at 256 it is three times ahead.
The machine's role decides the engine: agents and a few power users, Strata; a crowd, vLLM.

## Configuration in effect, Q8_0

`setup.sh --family unsloth --model Q8_0`, otherwise identical flags; `setup.sh` converts 460
tensors into the engine's form (max error 0.0144) and keeps the 54 GB n-gram table in RAM.
Experts 119.5 GiB, loaded at 18.7 GiB/s in 70 s, 100 % resident; **45–47 GB of VRAM per
card**, ready after 95 s.

| Output tok/s | Q8_0 | IQ3_S | Q8_0 / IQ3_S |
|---|---|---|---|
| Single stream, thinking on / off | 187.2 / 125.7 | 225.3 / 140.2 | 0.83 / 0.90 |
| Decode | 168–222 | 222–254 | ≈ 0.8 |
| Prefill 64k / 128k / 250k | 14,536 / 17,050 / 17,757 | 16,967 / 20,639 / 21,873 | 0.86 / 0.83 / 0.81 |
| C=8 / C=16, thinking on | 564.2 / 582.7 | 645.5 / 722.1 | 0.87 / 0.81 |

**The reference precision costs 13–19 % everywhere and still beats vLLM's FP8 with its MTP
draft on the single stream (187 against 175) and at C=8 (564 against 517).** What the 3 bits cost in answers: [5.5 points on MMLU-Pro
without thinking, nothing visible elsewhere](scenarios/quality.md).

## Scenarios

| Scenario | Status |
|---|---|
| [single-stream](scenarios/single-stream.md) | measured — **225.3 output tok/s** thinking on, 140.2 off, decode 222–254, cards at 20–34 % |
| [concurrent-load](scenarios/concurrent-load.md) | measured — levels 1 / 4 / 8 / 16 (deviation: 8 slots): **645.5 tok/s at C=8**, 722 at 16, queueing above; ahead of vLLM to C=8, level at 16 |
| [reasoning-cost](scenarios/reasoning-cost.md) | measured — thinking 2.5× in answers/s at C=8 |
| [long-context](scenarios/long-context.md) | measured — **16,967 / 20,639 / 21,873 tok/s prefill** at 64k / 128k / 250k, 3 of 3 needles each |
| [quality](scenarios/quality.md) | measured for both packs — IQ3_S: HumanEval 0.988 / 0.988, IFEval 0.910 on, **MMLU-Pro 0.820** off; Q8_0: MMLU-Pro 0.875 / 0.875, IFEval **0.945** on, HumanEval 0.957 / 0.982. **The 3 bits cost 5.5 points on MMLU-Pro without thinking** and nothing visible elsewhere |
