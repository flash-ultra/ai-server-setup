# Qwen3.8-27B

The dense 27 B release at **BF16** on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Set up and measured 2026-10-23.

| | |
|---|---|
| Checkpoint | [`Qwen/Qwen3.8-27B`](https://huggingface.co/Qwen/Qwen3.8-27B) |
| Size on disk | 51.8 GiB |
| Architecture | `Qwen3_5ForConditionalGeneration`, 64 layers, **dense** |
| Quantisation | **none** — BF16 |
| Native context | 262,144 · **262,144 served here** |
| Modality | text **and images**, native vision tower |

## Verdict

**The best answers measured on this machine, and the slowest serving of any model in
the table.** Both halves are now measured, and they point opposite ways.

On quality it beats [DeepSeek-V4-Flash-0731](../deepseek-v4-flash-0731/) — 284 B against
27 B, on the same cards, same protocol, same day — in **four of five benchmarks with
thinking on**, and loses four of five with thinking off — in both cases by margins too
small for 200 samples to establish, which is itself the point. It is also the first model here
that needs no quantisation, sees images without a second container, and leaves enough
room on the two cards for an embedding model beside it.

| Protocol [`q1`](vllm/scenarios/quality.md), thinking **on** | this model | DeepSeek-0731 |
|---|---|---|
| HumanEval | **0.982** | 0.963 |
| IFEval `prompt_strict` | **0.920** | 0.895 |
| IFEval `inst_strict` | **0.943** | 0.928 |
| GSM8K | **0.990** | 0.970 |
| MMLU-Pro | 0.850 | **0.870** |

**None of those five margins clears twice the standard error of the difference**, the
largest being 2.5 points against a resolution of roughly 5. The table says "not
measurably behind a model ten times its size", which is the finding — not "ahead". The
one result here that does clear its error bar by a wide margin is the arm comparison
*within* this model: thinking is worth **+13.5 points** on IFEval `prompt_strict`, far
more than it buys anywhere else.

**The other half of the decision is speed, and there it loses.** The full `v1` series
ran 2026-10-24, both arms, and DeepSeek is ahead in every cell:

| at concurrency 256 | this model **on** | DS **on** | this model **off** | DS **off** |
|---|---|---|---|---|
| [Answers/s](vllm/scenarios/concurrent-load.md) | 9.43 | **10.97** | 13.45 | **32.58–32.65** |
| [Output tok/s](vllm/scenarios/concurrent-load.md) | 1821.0 | **3583.8** | 718.0 | **1173.2–1182.6** |
| Latency p50 | 34.89 s | **27.58 s** | 19.94 s | **7.95–7.96 s** |

**On prefill the handicap is a steady 0.6×**:
[5131 / 4343 / 4207 tok/s](vllm/scenarios/long-context.md) against 8227 / 7480 / 7133 at
64k, 128k and 180k. A dense 27 B model reads all 25.9 GiB of its per-card weights for
every token; a 284 B mixture-of-experts reads a fraction of itself. **Parameter count
does not predict serving speed; active parameter count does**, and here the small model
is the slow one.

**Decode measured properly is 49.5 tok/s**, identical in both thinking arms over four
runs — see
[single stream](vllm/scenarios/single-stream.md#decode-rate-measured-separately).
DeepSeek has no separate decode figure on these two cards, so the 0.6× is about prefill
only.

**Where it is not behind is depth.** 3 of 3 needles at 64k, 128k, 180k **and 240k** —
the deepest verified retrieval in this repository, since nothing else here was taken
past 180k.

## What it changes operationally

**Images stop being an architecture problem.** On this machine, serving images alongside
DeepSeek-0731 needed a separate llama.cpp container, a persistent image store and an MCP
tool, because [nothing fits beside that checkpoint](../README.md#two-cards-set-a-hard-ceiling-on-model-size).
Here the vision tower is in the weights that load anyway.

**A second model fits.** [`Qwen3-Embedding-8B`](../qwen3-embedding-8b/) runs on the same two cards at
`--gpu-memory-utilization 0.14` while this one holds `0.82`, 95,230 of 97,887 MiB per
card in total. That cost three points of utilisation and 91,482 tokens of KV pool — the
details are in the [setup README](vllm/README.md#configuration-in-effect).

**The thinking switch is inverted relative to DeepSeek.** Thinking is **on** by default
here and off by default there, and the key that works on one is silently ignored by the
other. A gateway alias copied across does not fail; it serves the wrong arm. The field
carrying the thinking text is also named differently —
[`reasoning`, not `reasoning_content`](vllm/README.md#the-reasoning-text-is-in-reasoning-not-reasoning_content) —
which breaks the documented way of checking which arm you are on.

## Setups

| Setup | Status |
|---|---|
| [vLLM 0.28.0, unpatched](vllm/) | in production — quality measured, throughput not |

## Scenario coverage

| Scenario | vLLM TP=2 |
|---|---|
| [single-stream](vllm/scenarios/single-stream.md) | measured, both arms |
| [concurrent-load](vllm/scenarios/concurrent-load.md) | measured, both arms, full ladder |
| [long-context](vllm/scenarios/long-context.md) | measured, four depths to 240k |
| [reasoning-cost](vllm/scenarios/reasoning-cost.md) | measured, three variants |
| [quality](vllm/scenarios/quality.md) | measured, both arms |

**The only setup here complete under both `v1` and `q1`** — which is what makes the
trade it offers legible at all.
