# DeepSeek-V4-Flash-0731

The 0731 release on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-08-30, extended 2026-09-22.

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

| | Measured, thinking **off** |
|---|---|
| Peak measured | **39.62 answers/s · 1,436.5 output tok/s at concurrency 512** |
| Latency there | p50 **15.66 s**, both cards at 98 % |
| At concurrency 256 | 32.10–32.65 answers/s · 1,159.9–1,182.6 output tok/s, p50 7.96 s, three runs |
| Single stream | 2.08–2.12 req/s, 75.3–75.5 tok/s, p50 **0.47 s**, two runs |
| Prefill | 8227 tok/s at 64k · 7480 at 128k · 7133 at 180k |
| Needles | 3 of 3 at 64k, 128k and 180k |
| Run-to-run spread | **≤ 5 %** on the ladder, 0.3 % on single stream across 23 days |

**The ladder had not flattened when it stopped.** 512 concurrent requests give 22 % more
answers and 24 % more tokens than 256, at 98 % GPU. Anything quoted at 256 — including
the machine and repository tables — is the protocol ceiling, not the machine's.

| | Measured, thinking **on** |
|---|---|
| At concurrency 256 | 10.97 answers/s · **3,583.8 output tok/s**, p50 27.58 s |
| Tokens per answer | **327**, against 36 with thinking off |

**Thinking is off by default in this setup.** Turning it on multiplies output tokens per
second by 3.1 and divides answers per second by 3.0, because answers grow 9.1×. Both
tables above are the same server on the same day; neither is the model being faster.
Which one applies depends on the workload, and **no comparison against another model is
meaningful without naming the arm** — see
[concurrent load](sglang/scenarios/concurrent-load.md#reading) and
[reasoning cost](sglang/scenarios/reasoning-cost.md).

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

- **Speculative decoding not configured.** DSpark runs on the
  [four-card setup](../../cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/sglang/README.md)
  and nothing here uses it. That setup measures 131.2 tok/s single-stream against 75.3
  here — a gap currently attributed to card count, though speculation is an untested part
  of it. The cheapest remaining experiment with real upside.
- **`--mem-fraction-static` never swept.** 0.93 was carried over from the NVFP4 setup;
  `0.85` is known to fail. Where the floor actually sits decides whether anything can run
  beside this model — see the [setup README](sglang/README.md#still-open).
- **Levels above 512**, where the ladder was still climbing.
- **The full 1M context.** The pool holds 1,382,912 tokens, but `--context-length` is
  262,144, so reaching it needs a restart rather than a longer prompt.
- **No quality measurement**, in either thinking arm.
