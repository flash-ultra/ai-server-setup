# Measurement protocol

Every number in this repository comes from `bench.py`. The point of pinning the
protocol is that series stay comparable — across engines, across models, across
machines. Numbers produced with different parameters are a different series and must
say so.

**Current protocols: `v1` for throughput, `q1` for quality.**

## Usage

```bash
./bench.py --url http://localhost:8000 --model <served-name> --scenario concurrent
./bench.py --url http://localhost:8000 --model <served-name> --scenario single
./bench.py --url http://localhost:8000 --model <served-name> --scenario reasoning
./bench.py --url http://localhost:8000 --model <served-name> --scenario longctx
```

Standard library only, no dependencies. Targets any OpenAI-compatible
`/v1/chat/completions`. An engine that enforces a key reads it from `BENCH_API_KEY`
in the environment, which keeps it out of the process list and the shell history;
unset, no `Authorization` header is sent. Output is Markdown tables that go straight
into a scenario document, prefixed with a comment recording the protocol version.

## What is fixed

| Parameter | Value | Why it is pinned |
|---|---|---|
| `max_tokens` | 512 | Reasoning models spend most of the budget on thinking; at 200 the visible answer gets truncated and answers/s is inflated |
| Concurrency levels | 1, 8, 16, 32, 64, 128, 256 | Powers of two; the default series. `--levels` overrides it per run for configuration sweeps — every other parameter stays pinned, and the deviation is written into the output header. A run with overridden levels is still `v1`; state the override in the scenario's Method section |
| Measurement window | 40 s per level | Long enough to fill the batch, short enough for a full sweep |
| Warmup | 3 requests per level, discarded | The first request after start ran 21.55 s against 1.86 s afterwards |
| Token counting | `usage` fields | Stream deltas miss reasoning tokens — this was off by a factor of 5 once |
| Reasoning share | `usage.completion_tokens_details.reasoning_tokens` | **Engine-dependent, not model-dependent.** SGLang and vLLM report it; llama.cpp does not send the field at all, so the share reads 0 % even where the model puts every token into thinking. A 0 % in a llama.cpp row means "not reported", never "did not think" — and never compare this column across engines. **Verify against this `usage` field, not against a message field**: the name of the field carrying the thinking text differs per engine, see below |
| Sampling | `temperature 1.0`, `top_p 1.0` | Checkpoint calibration for DeepSeek-V4; note deviations per model |
| Prompt | verbatim in `bench.py` | See below |
| Prompt language | English | Applies from v1 on; the DeepSeek series below was measured with a German prompt of the same shape |

## Why the prompt itself is pinned

Fixing the token count is not enough. With speculative decoding, draft acceptance
depends on how predictable the text is — the same 1000 tokens of repetitive prose and
of dense code produce different throughput. The prompt is therefore stored verbatim in
`bench.py`, not described by its length.

Keep it stable across models. Changing the wording produces a different series even at
identical token counts, so a change means bumping the protocol version and re-measuring
the baseline, not quietly editing the string.

## Scenarios

**`single`** — concurrency 1, no competing load. The interactive single-user case.

**`concurrent`** — the full sweep, plus a mixed-traffic run at concurrency 32. The mix
draws from five request shapes (short question, code review, long analysis, tool-call
formulation, mid-length prose) at random per request, to approximate agent traffic.
Equal weights, no claim that this matches any particular production workload.

**`reasoning`** — cost per answer with thinking on, with `reasoning_effort=low`, and
with thinking off, at concurrency 8 and 32. Only meaningful for reasoning models;
skip it for others and say so in the model README.

> **The key that disables thinking belongs to the checkpoint, not to the protocol.**
> `--thinking-key` selects it; the default is `thinking`, which is what DeepSeek-V4
> uses. Gemma-4 needs `enable_thinking`. Some templates carry no switch at all.
>
> An unknown key is **accepted and silently ignored** — the request succeeds, thinking
> stays on, and the row reads as "disabling thinking changes nothing". That is a false
> negative, not a measurement. Verify against the model before running the scenario:
> send one request with and one without the key and compare
> `usage.completion_tokens_details.reasoning_tokens`. If it does not go to zero, the key
> is wrong or absent.
>
> **Compare the `usage` field, not a message field.** The name of the message field that
> carries the thinking text is engine-specific: SGLang uses `reasoning_content`, vLLM
> 0.28 uses **`reasoning`**. A check written against the wrong name finds nothing in
> *either* arm and reports the key as working when it was never tested — the same false
> negative one layer further out. Measured on
> [Qwen3.8-27B](../cloudscale-gpu2-256-40-2-1600/qwen3-8-27b/vllm/README.md#the-reasoning-text-is-in-reasoning-not-reasoning_content).

**`longctx`** — needle-in-a-haystack at full length. Filler is calibrated against the
server's own tokeniser, then three codes are planted at 10 %, 50 % and 90 %. The
middle needle is the actual test: models that only attend to the edges recover the
outer two and miss it. Reports prefill duration, throughput and how many needles came
back.

## Rules for comparison

**Same protocol version, or no comparison.** A table produced under `v1` cannot be
placed next to one produced under different parameters without saying so. If you must
compare across versions, compare requests per second and TTFT — those are less
sensitive to `max_tokens` than token throughput is.

**Re-measure the baseline when the protocol changes.** Do not retrofit old numbers.

**Record what the server was doing.** Engine version, parallelism configuration and
any per-request options belong in the scenario's Method section, not just the model
name.

**One measurement is not a result** where variance matters. Concurrency 128 was
measured twice with 6 % spread; that is worth stating rather than hiding.

## Quality: protocol `q1`, measured with Inspect AI

`v1` measures throughput and says nothing about whether answers are right. Quality is
a separate protocol with its own pinned parameters, because it uses a different tool
and a different notion of a run.

**Tool:** [Inspect AI](https://inspect.aisi.org.uk/) by the UK AI Security Institute,
with the `inspect_evals` benchmark collection. Installed per machine in its own venv
via `uv` — not `pip`, see the machine README.

| Parameter | Value | Why it is pinned |
|---|---|---|
| Benchmarks | `gsm8k`, `ifeval`, `mmlu_pro`, `humaneval` | Multi-step arithmetic, instruction following, domain knowledge, code. The four shapes an agent workload actually hits |
| Sample limit | 200 per benchmark, HumanEval 164 (its full set) | A full MMLU-Pro run is 12,000 samples and takes hours. 200 keeps stderr near 0.025, which is small enough to separate models that differ by more than ~5 points |
| `--max-connections` | 32 | Matches a level of the `v1` ladder, so the server is in a comparable state |
| `--max-tokens` | **50,000** | A thinking model with no cap generates toward the context window and the run never ends; a cap set too low silently truncates and the benchmark grades the truncation as a wrong answer. 50,000 was binding for 1 sample in 200 on the longest benchmark measured here |
| `-M client_timeout` | **3600** | A thinking answer measured here took 614 s against the OpenAI client's own 600 s default, which produced 50 retries and no result. Note this is **not** Inspect's `--timeout`, which already defaults to no timeout — the limit sits in the provider's HTTP client and has to be passed through with `-M`. It must clear the slowest single answer, not the median |
| Endpoint | the engine directly, **not** the gateway | litellm, HAProxy and their timeouts are not part of the model |
| Thinking | **both arms, always** | The whole point. A quality number without a stated thinking state is not comparable |
| Model string | `openai-api/<name>/<served-name>` | Works against any OpenAI-compatible engine; `vllm/` and `sglang/` providers would make Inspect start its own server |

```bash
export CYBL_BASE_URL=http://127.0.0.1:8001/v1
export CYBL_API_KEY=dummy
inspect eval inspect_evals/gsm8k --model openai-api/cybl/cyberlink \
  --limit 200 --max-connections 32 --max-tokens 50000 \
  -M client_timeout=3600 [--reasoning-effort low]
```

**Which flag switches thinking is per model**, exactly as in the `reasoning` scenario
of `v1`, and it has to be verified before the run rather than assumed — against
`usage.completion_tokens_details.reasoning_tokens`, which every engine here reports,
never against a message field whose name varies by engine. For DeepSeek-V4-Flash
`--reasoning-effort low` turns thinking **on** (default off): 2 completion tokens
without it, 82 with it, same question. For Qwen3.8-27B thinking is **on** by default and
`enable_thinking: false` turns it off: 93 reasoning tokens down to 0, while the
DeepSeek key `thinking: false` leaves it at 132.

**IFEval needs an extra dependency** that is not pulled in by `inspect-evals`:
`uv pip install "git+https://github.com/josejg/instruction_following_eval"`. Without
it the run aborts with an `AssertionError` after the model has already answered — so
install it first, or lose the time twice.

**Report the metric the benchmark defines, not a derived one.** IFEval has four:
`prompt_strict`, `prompt_loose`, `inst_strict`, `inst_loose`. The strict ones are the
honest ones; quote them and say which.

**Check why each answer stopped before using the score.** This is a reporting
obligation, not a nicety: an answer cut off at the token cap is graded wrong, and the
run reports an ordinary accuracy with an ordinary standard error. Nothing in the output
distinguishes "the model was wrong" from "the model was interrupted". Measured on one
cell of one benchmark, the difference between a cap of 8,192 and one of 50,000 was
**9.5 points** — 0.755 against 0.850, with 38 of 200 samples truncated in the first.

```bash
python3 - <<'PY'
import json, zipfile, glob, os, collections
for f in sorted(glob.glob(os.path.expanduser("~/logs/*.eval")), key=os.path.getmtime):
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

A run that reports anything other than `{'stop': n}` is not a result. Either raise the
cap and repeat it, or quote the score with the truncation count beside it — never the
score alone. **Also check that `n` equals the sample limit:** a run killed by a client
timeout finishes with fewer samples and still prints a table.

**These three parameters were added after the first two models were measured**, which is
why neither series ran under them. Both were re-checked against the criterion rather
than re-measured: every DeepSeek cell in both arms, the whole Qwen thinking-off arm, and
Qwen's GSM8K and IFEval thinking-on report `{'stop': n}` at the full sample count. The
single exception is 1 of 200 on Qwen's MMLU-Pro thinking-on, which is
[stated where the number is](../cloudscale-gpu2-256-40-2-1600/qwen3-8-27b/vllm/scenarios/quality.md#an-abort-reason-that-reads-as-a-quality-result).
Checking an old run against a new requirement is weaker than having measured under it,
and it is the most that can honestly be claimed for these two series.

**Sample limits are part of the result.** A `q1` figure at 200 samples is not
comparable to a published figure over the full set, and the numbers here are not
meant to be compared against vendor benchmark tables — only against each other, on
this hardware, with these limits.

## Known deviations in existing documents

The DeepSeek-V4-Flash-0731 series predates this protocol and is not fully consistent
with it:

| Document | Deviation |
|---|---|
| `llama-cpp/scenarios/*` | `max_tokens` 200, counted via stream deltas |
| all DeepSeek scenarios | German prompt text; `v1` uses an English prompt of the same structure |
| `sglang/scenarios/concurrent-load.md` | `max_tokens` 512, `usage` counting; levels above 128 measured in a later run |
| Model README verdict table | requests/s and TTFT only — both runs used `max_tokens` 200 and stream counting, which is why that particular comparison holds |

Throughput figures between the two setups are therefore **not** directly comparable;
the requests-per-second and TTFT comparison is. Anything measured from now on uses
`v1`.
