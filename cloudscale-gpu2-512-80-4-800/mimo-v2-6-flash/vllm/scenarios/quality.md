# Scenario: quality (`q1`) — vLLM TP=4

GSM8K, IFEval, MMLU-Pro and HumanEval at 200 samples (HumanEval 164), both thinking arms.

**Setup:** [vLLM 0.33.0 TP=4](../README.md) · `MiMo-V2.6-Flash-RL` · [the four-card machine](../../../README.md) · measured 2026-11-06, 17:18–17:58

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
Inspect AI 0.3.283, `--limit 200 --max-connections 32 --max-tokens 50000 -M client_timeout=3600`,
thinking off via `--reasoning-effort none` (verified: 3 → 0 reasoning tokens), HumanEval in
Inspect's Docker sandbox.

**Deviation: the effective cap was 32,768, not 50,000.** The server runs with
`--override-generation-config '{"max_new_tokens": 32768}'` (without it the checkpoint caps
every reply at 2,048, see the [setup](../README.md)), and vLLM takes the smaller of that
default and the request's `max_tokens`. All eight truncated answers below stopped at exactly
32,768 tokens. A re-run with a higher server default would settle those eight.

## Result

| Benchmark | thinking **off** | thinking **on** | Stop reasons |
|---|---|---|---|
| GSM8K | 0.945 ± 0.016 | **0.975** ± 0.011 | off 200 `stop`; on 199 `stop`, 1 at the cap |
| IFEval `prompt_strict` | 0.840 ± 0.026 | 0.850 ± 0.025 | off 200 `stop`; on 199 `stop`, 1 at the cap |
| IFEval `inst_strict` | 0.896 ± 0.017 | 0.903 ± 0.016 | |
| MMLU-Pro | 0.775 ± 0.030 | **0.850** ± 0.025 | off 200 `stop`; **on 194 `stop`, 6 at the cap** |
| HumanEval | 0.933 ± 0.020 | **0.963** ± 0.015 | 164 / 164 `stop` both arms |

The on-arm MMLU-Pro is a floor: with all six truncated answers right it would be 0.880.

## Against Qwen3.8-Flash-Next on the same cards

| | MiMo-V2.6-Flash-RL FP8 | [Qwen3.8-Flash-Next FP8](../../../qwen3-8-flash-next/vllm/scenarios/quality.md) |
|---|---|---|
| GSM8K off / on | 0.945 / 0.975 | 0.980 / 0.990 |
| IFEval prompt_strict off / on | 0.840 / 0.850 | 0.825 / **0.930** |
| MMLU-Pro off / on | 0.775 / 0.850 ‡ | **0.885** / 0.860 † |
| HumanEval off / on | 0.933 / 0.963 | 0.939 / 0.976 |

‡ six of 200 at the 32,768 cap · † two of 200 at the 50,000 cap

**Without thinking MiMo trails by 11 points on MMLU-Pro; with thinking it closes to within
one standard error.** The short reasoning that buys its 54 answers per second
([concurrent-load](concurrent-load.md)) costs it on stored knowledge, and thinking is how it
pays that back. On instruction following thinking does nothing for MiMo (0.840 → 0.850)
where it lifts Qwen by ten points. Code and arithmetic are level within the error bands.
