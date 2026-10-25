# DeepSeek-V4.1-Flash-1017 · EXL3 3-bit

A 763 B mixture-of-experts quantised to 3 bits per weight and packaged for exactly this
hardware, served on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-10-25.

| | |
|---|---|
| Pack | [`diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000`](https://huggingface.co/diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000) |
| Base model | [`deepseek-ai/DeepSeek-V4.1-Flash-1017`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) |
| Size on disk | 315 GiB, pack including recipe and drafter |
| Parameters | 763.2 B total, 384 routed experts, 6 active; Engram lookup tables 196.6 B |
| Quantisation | EXL3 3 bpw routed experts, int4 Engram, EXL3 3-bit DSpark drafter |
| Native context | 1,048,576 — measured in full, served at 327,680 |
| Modality | text and images |
| Speculation | DSpark drafter, `k=5`, on by default |

## Verdict

**First model on this machine that is best-in-class on prefill, competitive on decode,
and serves images and a 320k window at the same time.** It is also the only one here
whose checkpoint was built for this exact card count — the pack ships a recipe that
compiles its own sm120 kernels, and the configuration behind the author's numbers is the
script's default rather than something to be reconstructed.

| | Measured |
|---|---|
| Prefill, 180k tokens | **11,386 tok/s**, TTFT 15.8 s |
| Prefill, 960k tokens | 9,123 tok/s, TTFT 105.2 s, **3 of 3 needles** |
| Decode at 1500 tokens | 114.2 / 128.4 tok/s |
| Single stream, `v1` | **136.5 tok/s** output, p50 **1.19 s** |
| Quality, `q1` thinking on | **first in three of five**, [full table](#quality-protocol-q1) |
| GPU utilisation | 96–98 % on both cards at concurrency 1 |

**It beats the previous prefill leader on this machine by 1.6×** — 11,386 against
DeepSeek-V4-Flash-0731's 7,133 at the same depth — and it does so while activating 6 of
384 experts from a 3-bit checkpoint. On decode it sits within the band of the two fastest
models here rather than ahead of them.

**The quality result is narrower than the throughput one.** Against
[Qwen3.8-27B](../qwen3-8-27b/) not one margin clears two standard errors in either
direction, so on this protocol the two are tied. Against
[MiniMax-M2.5](../minimax-m2-5/) and [DeepSeek-0731](../deepseek-v4-flash-0731/) several
margins do clear, all of them on code and instruction following.

**What the author reports and what was measured here differ on decode**, 224 tok/s
against 114–128. Both are honest and they are not the same measurement: the pack's figure
comes from an agentic replay workload with the code drafter, this one from the pinned
`v1` prompt with the released drafter. The
[single-stream page](vllm-exl3/scenarios/single-stream.md#why-the-packs-own-decode-figure-is-higher)
has the comparison.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm-exl3/`](vllm-exl3/) | [single](vllm-exl3/scenarios/single-stream.md) · [concurrent](vllm-exl3/scenarios/concurrent-load.md) · [reasoning](vllm-exl3/scenarios/reasoning-cost.md) · [long context](vllm-exl3/scenarios/long-context.md) · [quality](vllm-exl3/scenarios/quality.md) |

## Model-specific gotchas

**Two of five ways to switch thinking off work, and the model card names a sixth that
does not exist.** The protocol requires probing the key rather than assuming it, because
an unknown key is accepted and silently ignored. Same question each time:

| Request | `reasoning_tokens` |
|---|---|
| no switch (default) | 18 |
| top-level `thinking: false` | 13 |
| `chat_template_kwargs: {thinking: false}` | **0** |
| `chat_template_kwargs: {enable_thinking: false}` | **0** |
| `reasoning_effort: "low"` | 17 |
| `reasoning_effort: "50"` | rejected — `literal_error` |

The top-level `thinking` flag is the trap: it is the right *name* and the wrong *place*,
and 13 against 18 reads like a weak effect rather than no effect. **`reasoning_effort`
is a numeric 1–100 scale according to the pack's documentation and the engine rejects
anything but the named literals** — `"50"` comes back as a validation error, so that part
of the documentation does not describe this build.

Switching thinking off is worth **84 % more answers per second** at concurrency 8, and it
makes the visible answer *longer* — 399 characters against 246. See
[reasoning cost](vllm-exl3/scenarios/reasoning-cost.md).

**The default `--max-num-seqs` is 8, so a concurrency ladder above 8 measures a queue.**
The pack is tuned for a handful of long agentic sessions, not for fan-out. The `v1`
ladder was run anyway and its upper half is reported as what it is — queueing delay, not
saturation. The production configuration raises the slot count to 32.

**The 1 M window and a co-tenant do not fit together.** Everything in the scenario files
was measured at the pack's default 1,048,576-token window with 4.25 GiB of KV, which
leaves no room for a second model. Serving at 327,680 with 2 GiB is the configuration
that runs now; the [setup page](vllm-exl3/README.md#two-configurations-and-which-numbers-belong-to-which)
keeps the two apart.

**`CPU_EXPERTS=1` is unavailable on this host and it is a guest-CPU property, not a
choice.** The pack can compute host-resident experts on CPU cores instead of streaming
them over PCIe, which the author measures at +17 % agentic decode. It needs AVX-512.
This guest reports its CPU as `Intel Xeon E3-12xx v2 (Ivy Bridge)` with `avx` and
**neither AVX2 nor AVX-512**, so `check_host.sh` fails and the GPU-only path is the only
one available here. Every number in this directory is therefore the GPU-only path.

## Quality, protocol `q1`

Measured 2026-10-25, [full table](vllm-exl3/scenarios/quality.md). Thinking-on arm,
200 samples per benchmark (HumanEval 164), abort reasons checked — no truncation.

| Benchmark | this model | [Qwen 27 B](../qwen3-8-27b/) | [DS-0731](../deepseek-v4-flash-0731/) | [MiniMax](../minimax-m2-5/) |
|---|---|---|---|---|
| GSM8K | 0.970 | **0.990** | 0.970 | 0.985 |
| MMLU-Pro | **0.880** | 0.850 | 0.870 | 0.825 |
| HumanEval | **1.000** | 0.982 | 0.963 | 0.970 |
| IFEval `prompt_strict` | **0.955** | 0.920 | 0.895 | 0.855 |
| IFEval `inst_strict` | **0.969** | 0.943 | 0.928 | 0.909 |

**First in three of five, and 164 of 164 on HumanEval** — the only perfect cell in this
repository. Last in GSM8K by 2.0 points, which is inside the noise.

**Against Qwen3.8-27B nothing separates them.** The largest margin is 3.5 points on
IFEval `prompt_strict` against a two-standard-error band of 4.8; the closest call is
HumanEval, +1.8 against 2.0. A 763 B model and a 27 B model tie on this protocol —
which is the same finding the machine's other three models already produced, now with a
28× parameter spread instead of a 10× one.

**Against the other two the instruction-following margins are real**: +10.0 points of
`prompt_strict` over MiniMax against a band of 5.8, +6.0 over DeepSeek-0731 against 5.3.
That is the column that decides whether an agent run completes.
