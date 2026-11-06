# MiMo-V2.6-Flash-RL

Xiaomi's MiMo-V2.6-Flash-RL on all four cards of [this machine](../README.md), measured
2026-11-06. The same checkpoint ran on the
[two-card machine](../../cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/README.md) in October;
that series is the reference column throughout.

| | |
|---|---|
| Checkpoint | [`XiaomiMiMo/MiMo-V2.6-Flash-RL`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) — 177.7 GB, FP8 |
| Architecture | 309 B total, 15 B active, 256 experts (8 routed), 39 sliding-window + 9 global attention layers; loaded as **`MiMoV2OmniForCausalLM`** |
| Setup | [vLLM 0.33.0, TP=4, stock image](vllm/) |
| Context served | **262,144** (196,608 on two cards) |
| Modality | text and images (audio encoder loads, untested) |
| Thinking | on by default; off via `enable_thinking: false` or `reasoning_effort: "none"` |

## Verdict

**The highest throughput measured on this machine: 3,740 output tok/s and 55 answers per
second at 256 clients, with thinking on and a p50 under five seconds.** Thinking costs
this model little — 68 tokens per answer, a fifth of them scratchpad — so its answers per
second are three to five times those of Qwen3.8-Flash-Next at the same load.

| | four cards | [two cards](../../cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/README.md) | four / two |
|---|---|---|---|
| Single stream, thinking on | **140.2 tok/s**, p50 0.48 s | 114.3 tok/s, p50 0.57 s | 1.23 |
| Decode at 1,500 tokens | 143.3–143.5 tok/s | 118.4–118.7 tok/s | 1.21 |
| C=256, thinking on | **3,739.6 tok/s · 54.98 answers/s**, p50 4.77 s | 3,128.9 tok/s · 46.05 answers/s, p50 5.74 s | 1.19 |
| C=256, thinking off | **75.58 answers/s**, p50 3.44 s | — | |
| Prefill | 6,104 / 4,865 / 3,561 tok/s at 64k / 128k / 250k | 3,070 tok/s at 180k | ≈ 1.4 |
| Needles | 3 of 3 at 250k | 3 of 3 at 180k | |
| KV pool | **4,294,730 tokens**, 16.4 full-length requests | 197,494 tokens, 1.0 | 21.7 |

**Twice the cards buy a fifth more speed and twenty times the KV pool.** Decode is bound
by the all-reduce over PCIe at every step, and TP=4 has twice the hops of TP=2, so the
single stream barely moves. What changes is room: the two-card machine had 3.9 GiB of KV
per card and served one full-length request; here the pool takes sixteen.

**Prefill falls with length**, from 6.1 k tok/s at 64k to 3.6 k at 250k: nine of the 48
layers attend globally, and their cost grows with the square of the context. A 250,000-token
prompt waits 70 s for its first token. For long-document work this is the model's weak
column; Qwen3.8-Flash-Next under Strata reads the same prompt in 11 s.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [reasoning cost](vllm/scenarios/reasoning-cost.md) · [long context](vllm/scenarios/long-context.md) |
