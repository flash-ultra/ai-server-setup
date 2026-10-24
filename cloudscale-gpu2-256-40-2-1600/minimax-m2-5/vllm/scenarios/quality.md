# Scenario: quality — vLLM TP=2

Four benchmarks, one thinking state, because this checkpoint has no switch.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `MiniMax-M2.5-NVFP4` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-24

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
no deviations. Inspect AI 0.3.283 with `inspect_evals`, run on the machine against the
engine directly, 200 samples per benchmark, HumanEval its full 164,
`--max-connections 32`, `--max-tokens 50000`, `-M client_timeout=3600`.

**One arm only, and that is a property of the checkpoint.** The protocol requires both;
here the second does not exist. Four candidate switches were probed before the run and
[none reaches zero reasoning tokens](../README.md#thinking-cannot-be-switched-off-and-that-is-measured).
Every figure below is therefore a thinking-on figure and can only be set against another
model's thinking-on column.

One run per benchmark.

## Result

<!-- protocol q1 · Inspect AI 0.3.283 · 200 samples (HumanEval 164) · max-connections 32 -->

| Benchmark | thinking on (only state available) |
|---|---|
| GSM8K | 0.985 ± 0.009 |
| HumanEval | 0.970 ± 0.013 |
| IFEval `inst_strict` | 0.909 ± 0.016 |
| IFEval `inst_loose` | 0.921 |
| IFEval `prompt_loose` | 0.875 |
| IFEval `prompt_strict` | 0.855 ± 0.025 |
| MMLU-Pro | 0.825 ± 0.027 |

## Against the other two models measured under `q1`

All thinking on, same machine, same protocol, same sample limits.

| Benchmark | MiniMax 116 B | [Qwen3.8-27B](../../../qwen3-8-27b/vllm/scenarios/quality.md) 27 B | [DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/quality.md) 284 B |
|---|---|---|---|
| GSM8K | 0.985 | **0.990** | 0.970 |
| MMLU-Pro | 0.825 | 0.850 | **0.870** |
| HumanEval | 0.970 | **0.982** | 0.963 |
| IFEval `prompt_strict` | 0.855 | **0.920** | 0.895 |
| IFEval `inst_strict` | 0.909 | **0.943** | 0.928 |

**Last of the three in three benchmarks**, second in the other two. The 27 B dense model
is ahead of this 116 B mixture-of-experts in all five.

**One of those margins is the first in this repository to clear its error bar.** Qwen's
IFEval `prompt_strict` is 6.5 points above this setup against a two-standard-error band
of 6.3 — it clears by 0.2 points, which is as marginal as a result can be while still
counting. Every other margin on this page is inside the noise, including the 2.5 points
on MMLU-Pro where the band is 7.4.

**So the honest summary is one finding, not five.** On following a written instruction
exactly, a 27 B dense model at BF16 measurably beats a 116 B MoE at NVFP4 on this
hardware. Everything else here is a tie at 200 samples.

## Reading

**Instruction following is this setup's weak column**, 0.855 `prompt_strict` against
0.920 and 0.895 for the other two. Roughly one prompt in seven is not followed to the
letter, which for an agent loop is the number that decides whether a run completes —
and it is the discipline the model card leads with.

**Domain knowledge is the one where it is closest to being justified by size**, 0.825
against DeepSeek's 0.870 at 284 B, and there it is still last.

**Thinking is always on and always paid for.** The
[concurrency ladder](concurrent-load.md) shows 258 tokens per answer at 9.65–9.75
answers/s; there is no cheaper mode to fall back to for short factual turns. Against
DeepSeek-0731, which can switch, that is the structural difference rather than any
single benchmark score.
