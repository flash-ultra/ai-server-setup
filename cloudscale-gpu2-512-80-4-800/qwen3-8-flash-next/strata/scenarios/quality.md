# Scenario: quality (`q1`) — Strata, four cards

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), both thinking arms,
against Strata on `127.0.0.1:8080`, for the IQ3_S pack and the Q8_0 pack.

**Setup:** [Strata 0.2.11, four-card layer split, 8 slots](../README.md) ·
[the four-card machine](../../../README.md) · IQ3_S measured 2026-11-06, 12:24–13:28

## Method

Protocol [`q1`](../../../../../dist/benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-tokens 50000 -M client_timeout=3600`, **`--max-connections 8`**
instead of 32 because the engine has eight slots (the same deviation as on the Rocky two-card machine (2× RTX PRO 4500), which
used four). Thinking off is `--reasoning-effort none`, verified before the run (33 → 4 completion
tokens; Strata reports no `reasoning_tokens`, so the check reads completion tokens). HumanEval in
Inspect's Docker sandbox. Every cell finished with `stop` on every sample.

## Result, IQ3_S

| Benchmark | thinking **off** | thinking **on** | Stop reasons |
|---|---|---|---|
| GSM8K | 0.980 ± 0.010 | 0.985 ± 0.009 | 200 / 200 `stop` |
| IFEval `prompt_strict` | 0.830 ± 0.027 | **0.910** ± 0.020 | 200 / 200 `stop` |
| IFEval `inst_strict` | 0.887 ± 0.018 | **0.940** ± 0.014 | |
| MMLU-Pro | 0.820 ± 0.027 | **0.860** ± 0.025 | 200 / 200 `stop` |
| HumanEval | **0.988** ± 0.009 | **0.988** ± 0.009 | 164 / 164 `stop` |

## Against the FP8 checkpoint under vLLM on the same cards, and the same pack on the Rocky two-card machine (2× RTX PRO 4500)

| | IQ3_S · Strata · **this machine** | FP8 · vLLM · [same cards](../../vllm/scenarios/quality.md) | IQ3_S · Strata · Rocky 2× RTX PRO 4500 |
|---|---|---|---|
| GSM8K off / on | 0.980 / 0.985 | 0.980 / 0.990 | 0.985 / 0.990 |
| IFEval prompt_strict off / on | 0.830 / 0.910 | 0.825 / 0.930 | 0.825 / 0.930 |
| MMLU-Pro off / on | **0.820** / 0.860 | **0.885** / 0.860 † | 0.855 / 0.895 |
| HumanEval off / on | **0.988 / 0.988** | 0.939 / 0.976 | — |

† two of 200 truncated at the 50k cap.

**Ten of twelve comparable cells agree within one standard error; the two that do not point
in opposite directions.** MMLU-Pro with thinking off is the one cell where the 3-bit pack
trails the FP8 checkpoint by more than two standard errors (0.820 against 0.885), and the
same pack on the Rocky machine sits between them (0.855), so part of that gap is sampling.
HumanEval goes the other way: the 3-bit pack passes 162 of 164 in both arms, the FP8 run
154 and 160. Nothing here says the 3 bits cost anything a 200-sample protocol can see.

