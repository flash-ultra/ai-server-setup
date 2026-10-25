# Scenario: quality — vLLM + EXL3, TP=2

Four benchmarks against a 3-bit quantisation of a 763 B model, and the first comparison
on this machine where parameter count spans a factor of 28.

**Setup:** [vLLM + EXL3 plugin, TP=2](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3
3 bpw · [cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-25

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai).
Inspect AI 0.3.283 with `inspect_evals`, run **on the machine against the engine on
`127.0.0.1:8010`** — not through the gateway, so neither the router nor litellm is part
of the measurement. 200 samples per benchmark, HumanEval its full 164,
`--max-connections 32`, `--max-tokens 50000`, `-M client_timeout=3600`.

**The thinking arm was verified before the run**, as the protocol requires: the same
question returns 124 reasoning tokens by default and 0 with
`chat_template_kwargs: {thinking: false}`. Three other plausible keys leave thinking on
— the [probe table](../../README.md#model-specific-gotchas) lists all five.

**Abort reasons were checked after every run**, as the protocol requires. All four logs
report `{'stop': n}` with no truncation and no retries; the only warnings in them are
unauthenticated Hugging Face dataset downloads.

**Thinking-on arm only**, which is a deviation from the protocol and limits what the
table supports: every figure below is the default arm, and the machine's standing
finding that
[thinking is worth most on instruction following](../../../README.md#quality) is not
re-tested here. The switch itself is verified and
[measured for cost](reasoning-cost.md) — 84 % more answers per second at concurrency 8.

## Result

<!-- protocol q1 · Inspect AI 0.3.283 · 200 samples (HumanEval 164) · max-connections 32 · max-tokens 50000 -->

| Benchmark | thinking **on** | Run time |
|---|---|---|
| GSM8K | 0.970 ± 0.012 | 4 min 55 s |
| MMLU-Pro | 0.880 ± 0.023 | 29 min 48 s |
| HumanEval | **1.000** ± 0.000 | 6 min 52 s |
| IFEval `prompt_strict` | 0.955 ± 0.015 | 29 min 08 s |
| IFEval `inst_strict` | 0.969 ± 0.011 | — |
| IFEval `prompt_loose` | 0.955 ± 0.015 | — |
| IFEval `inst_loose` | 0.972 ± 0.009 | — |
| IFEval `final_acc` | 0.963 ± 0.019 | — |

**164 of 164 on HumanEval.** The only perfect cell in this repository, and the only
one whose standard error is zero — which also means the benchmark has stopped
discriminating at this level and cannot show a difference against anything above 0.982.

## Against the rest of the machine

Same machine, same protocol, thinking-on arm throughout. Each column is repeated from
its own scenario file: [Qwen3.8-27B](../../../qwen3-8-27b/vllm/scenarios/quality.md),
[DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/quality.md),
[MiniMax](../../../minimax-m2-5/vllm/scenarios/quality.md).

| Benchmark | this model 763 B | Qwen 27 B | DS-0731 284 B | MiniMax 116 B |
|---|---|---|---|---|
| GSM8K | 0.970 | **0.990** | 0.970 | 0.985 |
| MMLU-Pro | **0.880** | 0.850 | 0.870 | 0.825 |
| HumanEval | **1.000** | 0.982 | 0.963 | 0.970 |
| IFEval `prompt_strict` | **0.955** | 0.920 | 0.895 | 0.855 |
| IFEval `inst_strict` | **0.969** | 0.943 | 0.928 | 0.909 |

**First in three of five, second in one, last in one.** Counted by direction that is the
best result on this machine. Counted against the error bars it is narrower.

### What clears two standard errors

Against the standard error of the *difference* — `sqrt(se₁² + se₂²)`, larger than either
column's own — only the instruction-following and code margins survive:

| | margin | 2 × se of the difference | |
|---|---|---|---|
| vs **Qwen 27 B**, IFEval `prompt_strict` | +3.5 | 4.8 | inside |
| vs **Qwen 27 B**, IFEval `inst_strict` | +2.6 | 3.6 | inside |
| vs **Qwen 27 B**, MMLU-Pro | +3.0 | 6.8 | inside |
| vs **Qwen 27 B**, HumanEval | +1.8 | 2.0 | inside, barely |
| vs **Qwen 27 B**, GSM8K | −2.0 | 2.8 | inside |
| vs **MiniMax**, IFEval `prompt_strict` | **+10.0** | 5.8 | **clears** |
| vs **MiniMax**, IFEval `inst_strict` | **+6.0** | 3.9 | **clears** |
| vs **MiniMax**, HumanEval | **+3.0** | 2.6 | **clears** |
| vs **DS-0731**, IFEval `prompt_strict` | **+6.0** | 5.3 | **clears** |
| vs **DS-0731**, IFEval `inst_strict` | **+4.1** | 3.9 | **clears** |

MMLU-Pro and HumanEval for DeepSeek-0731 are published without a standard error in
[its own file](../../../deepseek-v4-flash-0731/sglang/scenarios/quality.md), so those
two rows are not in the table rather than computed from an assumed one.

**Against Qwen3.8-27B, nothing separates them.** Five benchmarks, 28× the parameters,
and not one margin clears its band in either direction — the closest is HumanEval at
+1.8 against 2.0, which fails by the width of a rounding step. This is now the third
pairing on this machine to land there, and the strongest version of the machine's
standing result: **parameter count buys nothing measurable in answer quality under
`q1`.**

**Against the other two it does separate, and only in one place.** Every margin that
clears is instruction following or code; none of the knowledge or arithmetic margins
do. Against MiniMax that is one prompt in seven not followed to the letter against one
in twenty-two.

**What this comparison costs on the other side is nothing.** Unlike the earlier pairs,
this model is not trading quality for speed: it holds the top prefill figure on the
machine and a decode rate inside the leading band. The
[single-stream page](single-stream.md#against-the-rest-of-the-machine) has that half.
