# Hy3 · FP8

Tencent's Hy3 on all four cards of [this machine](../README.md), measured 2026-11-07.

| | |
|---|---|
| Checkpoint | [`tencent/Hy3-FP8`](https://huggingface.co/tencent/Hy3-FP8) — 301 GB, FP8, Apache 2.0 |
| Architecture | `HYV3ForCausalLM` — 295 B total, 21 B active, 192 experts (8 routed plus one shared per token), 80 layers, GQA with 8 KV heads, one MTP layer |
| Setup | [vLLM 0.33.0, TP=4, FP8 KV](vllm/) |
| Context served | 262,144 (256K native) |
| Modality | text |
| Thinking | `reasoning_effort` `no_think` (template default) / `low` / `high`; this server defaults to `high` |

## Verdict

**Answers at DeepSeek's level, at the slowest pace on these cards.** With thinking at `high`,
`q1` gives MMLU-Pro 0.880, IFEval 0.940 and HumanEval 0.994, no difference to DeepSeek-V4.1
reaching two standard errors. It gets there with ten times the tokens of its `no_think` mode,
a median of 2,871 per MMLU-Pro answer, and both quality arms took 101 minutes where Beam's took 30.

| Thinking on | Hy3 FP8 | DeepSeek-V4.1 EXL3 | Beam-1.0 NVFP4 | MiMo-V2.6-Flash FP8 |
|---|---|---|---|---|
| Single stream | 89.6 tok/s | **153.2** | 98.2 | 140.2 |
| C=256, over the real run time | 2,254 tok/s · 4.4 answers/s | 1,510 · 9.2 | 2,972 · 12.8 | **3,650 · 53.7** |
| Prefill 250k | 1,763 tok/s | **13,264** | 4,616 | 3,561 |
| KV pool | 307,936 tokens | **4,538,321** | 2,123,633 | 4,294,730 |

**Under load it sits mid-field, and its answers do not finish.** At `high` every protocol
answer runs into the 512-token cap, so the 4.4 answers per second at 256 clients are cut-off
thinking. Decode is 85 tok/s and flat. **Long prompts are its weak side:** 1,763 tok/s of prefill
at 250k, 2 min 22 s to the first token, and a cache that holds 1.17 requests of full length,
because 280 GiB of weights leave about 12 GB per card.

**Without thinking it is a different model:** 56-token answers, 40 answers per second at 256
clients, and MMLU-Pro down from 0.880 to 0.795.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [long context](vllm/scenarios/long-context.md) · [quality](vllm/scenarios/quality.md) |

The `reasoning` scenario was not run: its thinking key is a boolean, and this template takes
three named levels.
