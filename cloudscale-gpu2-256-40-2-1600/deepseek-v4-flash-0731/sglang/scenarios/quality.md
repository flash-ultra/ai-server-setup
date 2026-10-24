# Scenario: quality — SGLang TP=2

Four benchmarks, both thinking arms, same engine and settings.

**Setup:** [SGLang TP=2](../README.md) · `DeepSeek-V4-Flash-0731` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-23

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai),
no deviations. Inspect AI 0.3.283 with `inspect_evals`, run **on the machine against
the engine on `127.0.0.1:8001`** — not through the gateway, so neither litellm nor
HAProxy is part of the measurement.

200 samples per benchmark, HumanEval its full 164, `--max-connections 32`.

**The thinking switch was verified before the run**, as the protocol requires: the
same question returns 2 completion tokens by default and 82 with
`--reasoning-effort low`. Thinking is **off** by default in this setup, so the flag
turns it **on** — the opposite direction from MiMo.

## Result

<!-- protocol q1 · Inspect AI 0.3.283 · 200 samples (HumanEval 164) · max-connections 32 -->

| Benchmark | thinking **off** | thinking **on** | Δ |
|---|---|---|---|
| GSM8K | **0.985** ± 0.009 | 0.970 ± 0.012 | −1.5 |
| MMLU-Pro | 0.845 ± 0.026 | **0.870** | +2.5 |
| HumanEval | 0.939 | **0.963** | +2.4 |
| IFEval `prompt_strict` | 0.810 ± 0.028 | **0.895** ± 0.022 | **+8.5** |
| IFEval `inst_strict` | 0.874 ± 0.018 | **0.928** ± 0.016 | +5.4 |
| IFEval `prompt_loose` | 0.860 ± 0.025 | **0.930** ± 0.018 | +7.0 |
| IFEval `inst_loose` | 0.909 | **0.953** | +4.4 |

## Reading

**Thinking buys instruction following, not arithmetic.** The largest gain by far is
IFEval `prompt_strict` at +8.5 points — following a format, honouring a constraint,
not skipping a requirement. For an agent workload that is the column that matters,
and it is the one nobody looks at.

**GSM8K gets worse with thinking, and that is probably real but small.** 0.985 → 0.970
at stderr 0.009 and 0.012. The two intervals overlap, so this is at the edge of what
200 samples can resolve; it is reported because it was measured, not because it is
established. Grade-school arithmetic is easy enough that extra deliberation has more
room to introduce an error than to prevent one.

**Code and knowledge gain moderately**, +2.4 and +2.5 points.

**This is the other half of the thinking trade-off.** The
[reasoning cost](reasoning-cost.md) scenario measures what thinking costs: a factor of
four in answers per second. Until now the repository only documented that side. The
table above is what is bought with it — and for IFEval the answer is a lot.

**Which arm to run is therefore a workload decision, not a default.** Short factual
turns at high concurrency: off. Agent loops that must honour a format and a plan:
on, and accept a quarter of the throughput.
