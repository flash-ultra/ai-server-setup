# Scenario: quality (`q1`) — vLLM TP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), at `reasoning_effort`
low and at the default (max).

**Setup:** [vLLM 0.33.0 TP=4 EP, NVFP4](../README.md) · `GLM-5.3-Flash` · [the four-card machine](../../../README.md) · measured 2026-11-06, 18:37–19:48

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
HumanEval in Inspect's Docker sandbox. **Deviation: the thinking-off arm is replaced by
`--reasoning-effort low`.** GLM-5.3-Flash ignores both off switches
([pinned values](../README.md#pinned-values)); `low` is the lowest setting it honours and
cuts thinking to 2–4 % of the answer ([reasoning cost](reasoning-cost.md)).

## Result

| Benchmark | effort **low** | effort **max** (default) | Stop reasons |
|---|---|---|---|
| GSM8K | 0.985 ± 0.009 | 0.985 ± 0.009 | 200 / 200 `stop` both |
| IFEval `prompt_strict` | 0.810 ± 0.028 | **0.880** ± 0.023 | 200 / 200 `stop` both |
| MMLU-Pro | 0.815 ± 0.028 | **0.870** ± 0.024 | 200 / 200 `stop` both |
| HumanEval | 0.939 ± 0.019 | **0.970** ± 0.013 | low 164 `stop`; max 163, 1 at the 50,000 cap |

## Against the other models on the same cards

| | GLM-5.3-Flash NVFP4 · low / max | [MiMo-V2.6-Flash-RL](../../../mimo-v2-6-flash/vllm/scenarios/quality.md) · off / on | [Qwen3.8-Flash-Next FP8](../../../qwen3-8-flash-next/vllm/scenarios/quality.md) · off / on |
|---|---|---|---|
| GSM8K | **0.985 / 0.985** | 0.945 / 0.975 | 0.980 / 0.990 |
| IFEval prompt_strict | 0.810 / 0.880 | 0.840 / 0.850 | 0.825 / **0.930** |
| MMLU-Pro | 0.815 / 0.870 | 0.775 / 0.850 ‡ | **0.885** / 0.860 † |
| HumanEval | 0.939 / 0.970 | 0.933 / 0.963 | 0.939 / 0.976 |

‡ six at the 32,768 cap · † two at the 50,000 cap

**At its default effort GLM sits level with Qwen on three of four benchmarks and five
points behind it on instruction following**; at `low` it keeps arithmetic and code and
drops 5–7 points on knowledge and instructions. The full thinking budget buys it no lead
anywhere, at six times the tokens per answer that Qwen spends and a sixth of its answer
rate under load ([concurrent-load](concurrent-load.md)).
