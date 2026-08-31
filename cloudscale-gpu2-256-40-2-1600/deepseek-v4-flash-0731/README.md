# DeepSeek-V4-Flash-0731

The 0731 release on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-08-30.

| | |
|---|---|
| Checkpoint | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) |
| Size on disk | 155.4 GiB (156 GB), 74 files |
| Architecture | `DeepseekV4ForCausalLM`, 43 layers, 256 experts, 6 active |
| Quantisation | `fp8` e4m3, block size 128×128 |
| Native context | 1,048,576 · **262,144 served here** |
| Modality | text only |

The same release measured on the [four-card machine](../../cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/),
here on half the cards. **Those numbers predate `v1`** and are not directly comparable;
this directory is a fresh `v1` series.

## Verdict

**The most stable thing measured on this machine, and the fastest under load — with one
caveat that decides how the number should be read.**

| | Measured |
|---|---|
| Peak under load | **32.58–32.65 answers/s at concurrency 256**, two runs |
| Latency at that point | p50 **7.96 s** |
| Single stream | 2.12 req/s, p50 **0.47 s** |
| Prefill, 180k tokens | 26.4 s, **6823 tok/s** |
| Needles at 180k | 3 of 3 |
| Run-to-run spread | **≤ 5 %**, 0 % at both ends of the ladder |

**Thinking is off by default in this setup**, and every headline number above was measured
that way — see [reasoning cost](sglang/scenarios/reasoning-cost.md). Answers come back at
35 tokens. Against a model that cannot switch thinking off, comparing answers per second
compares two different workloads.

Against [MiniMax-M2.5](../minimax-m2-5/) on the same cards, thinking on for both:

| at concurrency 32 | Answers/s | Output tok/s | Tokens/answer |
|---|---|---|---|
| MiniMax-M2.5 (79 % reasoning, not switchable) | 4.25 / 4.03 | 1247 / 1284 | 258 |
| DeepSeek-0731 with `reasoning_effort=low` (85 %) | 3.65 | 1017 | 279 |

MiniMax is ahead there. With thinking off, 0731 delivers 11.9 answers/s at the same level.
**The two are not interchangeable measurements**; which one applies depends on whether the
workload wants a thinking model.

## Measurements

| Setup | Scenarios |
|---|---|
| [`sglang/`](sglang/) | [single](sglang/scenarios/single-stream.md) · [concurrent](sglang/scenarios/concurrent-load.md) · [reasoning](sglang/scenarios/reasoning-cost.md) · [long context](sglang/scenarios/long-context.md) |

## Model-specific gotchas

**The KV cache must be FP8, and it runs without scaling factors.** `--kv-cache-dtype bf16`
is rejected at load:

```
AssertionError: bf16 is not supported for DeepseekV4ForCausalLM
```

FP8 is the only admissible setting, and SGLang then warns on every start:

```
Using FP8 KV cache but no scaling factors provided. Defaulting to scaling factors of 1.0.
This may lead to less accurate results!
```

Every number in this directory carries that caveat. It is not a configuration mistake —
it is the only option the architecture accepts in this build.

**`thinking: false` works, but it is already the default.** The protocol names `thinking`
as the DeepSeek-V4 key, and it does take effect. It just changes nothing here, because
this setup does not think unless asked. `reasoning_effort=low` is what turns it on.

**Reasoning share reads 0 % on the direct path.** SGLang does not report
`completion_tokens_details.reasoning_tokens` to a client talking to it directly; through a
litellm gateway with `--reasoning-parser deepseek-v4` the field is populated. A 0 % in
these tables means "thinking was off", verified against the `reasoning_effort=low` rows —
not "not reported".

## Still open

- **No quality measurement.**
- **The full 1M context is untested here.** `max_total_num_tokens` is 1,382,912, so a
  single 1M request fits the pool arithmetically. Concurrency would drop to one.
- **Speculative decoding not configured.** DSpark was measured on the four-card machine;
  nothing here uses it.
