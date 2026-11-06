# Scenario: quality (`q1`) — vLLM TP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval its full 164), both
thinking arms, against the engine on `127.0.0.1:8000`.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md) · `Qwen3.8-Flash-Next-FP8` ·
[the four-card machine](../../../README.md) · measured 2026-11-06, 10:47–11:45

## Method

Protocol [`q1`](../../../../../dist/benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai):
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
`q1-run.sh`. Thinking off is
`--reasoning-effort none`, verified before the run (45 reasoning tokens → 0). **HumanEval ran
for the first time in this series**: the machine has Docker, so Inspect's `--sandbox docker`
executes the generated code in a container, not on the host. Stop reasons checked with
`stopcheck.py` over the Inspect logs.

## Result

| Benchmark | thinking **off** | thinking **on** | Stop reasons |
|---|---|---|---|
| GSM8K (accuracy) | 0.980 ± 0.010 | **0.990** ± 0.007 | 200 / 200 `stop` both arms |
| IFEval `prompt_strict` | 0.825 ± 0.027 | **0.930** ± 0.018 | 200 / 200 `stop` both arms |
| IFEval `inst_strict` | 0.884 ± 0.019 | **0.950** ± 0.014 | |
| MMLU-Pro (accuracy) | **0.885** ± 0.023 | 0.860 ± 0.025 | off 200 `stop`; **on: 198 `stop`, 2 `max_tokens`** |
| HumanEval (pass@1) | 0.939 ± 0.019 | **0.976** ± 0.012 | 164 / 164 `stop` both arms |

**Two MMLU-Pro answers with thinking on hit the 50,000-token cap** and are graded wrong; the
0.860 is therefore a floor, at most 0.870 without the cap. The arms are inside each other's
error band on MMLU-Pro either way; on IFEval and HumanEval thinking buys 10 and 4 points.

## Against the same model as IQ3_S under Strata on the Rocky two-card machine (2× RTX PRO 4500)

Strata `q1`,
same protocol, four connections instead of 32, no HumanEval there (no sandbox):

| | FP8 · vLLM · this machine | IQ3_S · Strata · Rocky 2× RTX PRO 4500 |
|---|---|---|
| GSM8K off / on | 0.980 / 0.990 | 0.985 / 0.990 |
| IFEval prompt_strict off / on | 0.825 / 0.930 | 0.825 / 0.930 |
| MMLU-Pro off / on | 0.885 / 0.860 | 0.855 / 0.895 |
| HumanEval off / on | 0.939 / 0.976 | — |

**The 3-bit GSQ-RCO and the author's FP8 are indistinguishable under `q1`.** Six of six
comparable cells agree within one standard error; IFEval is identical to the third decimal
in both arms. MMLU-Pro swaps direction between the arms (off wins here, on wins there), which
at ± 0.025 is noise plus the two truncated answers. Whatever the 3-bit pack costs, 200
samples per benchmark cannot see it, and the Strata run on this machine will add the
Q8_0 reference to the same table.
