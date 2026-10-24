# Scenario: quality — vLLM TP=2

Four benchmarks, both thinking arms, and the first head-to-head against the model this
machine was serving until now.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `Qwen3.8-27B` BF16 ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-23

## Method

Protocol [`q1`](../../../../benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai).
Inspect AI 0.3.283 with `inspect_evals`, run **on the machine against the engine on
`127.0.0.1:8001`** — not through the gateway, so neither litellm nor HAProxy is part of
the measurement. 200 samples per benchmark, HumanEval its full 164,
`--max-connections 32`, `--gpu-memory-utilization 0.85`.

**The thinking switch was verified before the run**, as the protocol requires: the same
question returns 66 completion tokens by default and 4 with `--reasoning-effort none`.
Thinking is **on** by default here, so the flag turns it **off** — the opposite direction
from DeepSeek-0731, where the same protocol needs `--reasoning-effort low` to turn it on.

**Deviation from the DeepSeek run, stated because it is one:** six of the eight cells
below ran with no token cap, exactly as the DeepSeek series did. The two thinking-on
cells MMLU-Pro and HumanEval ran with `--max-tokens 50000 -M client_timeout=3600`,
because uncapped they did not finish. The cap is effectively non-binding at that
value — 1 of 200 samples and 0 of 164 reached it — so the comparison holds, but it is not
the identical command line. How the value was arrived at is below, and it is the reason
`q1` now pins both parameters.

## Result

<!-- protocol q1 · Inspect AI 0.3.283 · 200 samples (HumanEval 164) · max-connections 32 -->

| Benchmark | thinking **off** | thinking **on** | Δ |
|---|---|---|---|
| GSM8K | 0.975 ± 0.011 | **0.990** ± 0.007 | +1.5 |
| MMLU-Pro | 0.830 ± 0.027 | **0.850** ± 0.025 | +2.0 |
| HumanEval | 0.976 ± 0.012 | **0.982** ± 0.010 | +0.6 |
| IFEval `prompt_strict` | 0.785 ± 0.029 | **0.920** ± 0.019 | **+13.5** |
| IFEval `inst_strict` | 0.852 ± 0.021 | **0.943** ± 0.014 | +9.1 |
| IFEval `prompt_loose` | 0.830 ± 0.027 | **0.940** ± 0.017 | +11.0 |
| IFEval `inst_loose` | 0.887 ± 0.018 | **0.956** ± 0.013 | +6.9 |

## Against DeepSeek-V4-Flash-0731

Same machine, same protocol, same day, both arms stated. The DeepSeek column is
[its own scenario file](../../../deepseek-v4-flash-0731/sglang/scenarios/quality.md);
the numbers are repeated here only because a two-model comparison needs them side by
side.

| Benchmark | Qwen **off** | DS **off** | Qwen **on** | DS **on** |
|---|---|---|---|---|
| GSM8K | 0.975 | **0.985** | **0.990** | 0.970 |
| MMLU-Pro | 0.830 | **0.845** | 0.850 | **0.870** |
| HumanEval | **0.976** | 0.939 | **0.982** | 0.963 |
| IFEval `prompt_strict` | 0.785 | **0.810** | **0.920** | 0.895 |
| IFEval `inst_strict` | 0.852 | **0.874** | **0.943** | 0.928 |

**With thinking on, the 27 B dense model wins four of five.** Code by +1.9, instruction
following by +2.5 and +1.5, arithmetic by +2.0; it loses domain knowledge by 2.0.
Against a 284 B mixture-of-experts, at full precision, on half the hardware budget.

**With thinking off it loses four of five.** Every margin is small — 1.0 to 2.5 points
at a stderr near 0.02 — but the direction is consistent across four of the five rows,
and only HumanEval stays ahead, there by a wide 3.7.

**Not one of those five margins is statistically established, in either direction.**
Against the standard error of the *difference* — `sqrt(se_qwen² + se_ds²)`, which is
larger than either column's own — every row falls inside two standard errors:

| | margin | 2 × se of the difference |
|---|---|---|
| GSM8K | +2.0 | 2.8 |
| HumanEval | +1.9 | 3.6 |
| IFEval `inst_strict` | +1.5 | 4.3 |
| IFEval `prompt_strict` | +2.5 | 5.8 |
| MMLU-Pro | −2.0 | 7.2 |

At 200 samples the protocol resolves differences of roughly 5 points, and the largest
margin here is 2.5. **"Four of five" is a count of directions, not of results.** What
the table supports is that a 27 B dense model at BF16 is not measurably behind a 284 B
MoE in this arm — which is a real finding about model size, and a weaker claim than the
count suggests. Separating these models on quality needs a larger sample than `q1`
takes.

**So the two models do not rank; the two arms do.** The one difference here that clears
its own error bar by a wide margin is **within** this model: thinking against no
thinking on IFEval. An argument for either model has to name the arm first.

**What this comparison does not include is speed.** DeepSeek has a full `v1` series on
this machine and this setup has none at all. A quality table is half a decision; the
other half is unmeasured here.

## Thinking buys instruction following, and here it buys a great deal

The largest gain in the arm table is IFEval `prompt_strict` at **+13.5 points** —
0.785 to 0.920. Honouring a format, not skipping a requirement, obeying a constraint.
The same column on DeepSeek moves +8.5. For an agent workload that is the column that
decides whether a run completes, and it is the one nobody quotes.

GSM8K, MMLU-Pro and HumanEval move between +0.6 and +2.0, each within or at the edge of
twice their stderr. The instruction-following gain is the only one here that is large
compared to its own error bar.

**Note that thinking-off is the weak arm for exactly the thing it is usually chosen
for.** Short, cheap, high-concurrency turns are typically agent turns, and agent turns
are instruction-following turns. 0.785 means roughly one prompt in five is not followed
to the letter.

## An abort reason that reads as a quality result

The thinking-on MMLU-Pro cell was measured four times before it produced a usable
number, and the three failures are the reason `q1` now pins `max_tokens`,
`client_timeout` and an abort-reason check.

| Run | `--max-tokens` | Samples finished | Reached the cap | Score |
|---|---|---|---|---|
| 17:08 | none | 196 of 200 | — | **no result** — ran toward the 262,144 window, aborted |
| 17:40 | 8,192 | 200 | **38** | 0.755 — **invalid** |
| 17:57 | 24,576 | 189 of 200 | — | **no result** — answers took 614 s against the client's 600 s default, 50 retries |
| 18:47 | 50,000 | 200 | 1 | **0.850** — the number in the table |

**0.755 against 0.850 is 9.5 points of pure truncation**, and nothing in the run says
so. Inspect reports an accuracy and a standard error; a reply cut off mid-reasoning is
simply graded wrong. HumanEval did the same thing more quietly: 0.921 at 8,192 with 13
of 164 cut off, 0.982 at 50,000 with none.

**A thinking model's token budget is not a performance setting, it is a correctness
precondition.** Set it too low and the benchmark still produces a plausible, publishable,
wrong number — and the wrong number is lower, which is exactly the direction that gets
believed when a small model is being compared against a large one.

**The check costs one command** and belongs after every run, before the score is used:

```bash
python3 - <<'PY'
import json, zipfile, glob, os, collections
for f in sorted(glob.glob(os.path.expanduser("~/logs/*.eval")),
                key=os.path.getmtime):
    z = zipfile.ZipFile(f); fr = collections.Counter(); n = 0
    for nm in (x for x in z.namelist() if x.startswith("samples/")):
        try: d = json.loads(z.read(nm))
        except Exception: continue
        n += 1
        for ev in (d.get("events") or []):
            o = ev.get("output")
            if isinstance(o, dict):
                for ch in (o.get("choices") or []):
                    if ch.get("stop_reason"): fr[ch["stop_reason"]] += 1
    bad = sum(v for k, v in fr.items() if k != "stop")
    print(f"{os.path.basename(f)[:40]:42} n={n:4} {dict(fr)}"
          f"{'   <-- TRUNCATED' if bad else ''}")
PY
```

Run against every `q1` log on this machine, it reports `{'stop': n}` for all four
DeepSeek benchmarks in both arms, for the whole Qwen thinking-off arm, and for GSM8K and
IFEval thinking-on. The only surviving exception is the 1 of 200 in the row above.
**Every number on this page and on the DeepSeek page has been checked this way**, which
is not the same as having been measured under the pinned parameter — it is what can
honestly be said about runs that predate it.
