# Measurement protocol

Every number in this repository comes from `bench.py`. The point of pinning the
protocol is that series stay comparable — across engines, across models, across
machines. Numbers produced with different parameters are a different series and must
say so.

**Current protocol: `v1`**

## Usage

```bash
./bench.py --url http://localhost:8000 --model <served-name> --scenario concurrent
./bench.py --url http://localhost:8000 --model <served-name> --scenario single
./bench.py --url http://localhost:8000 --model <served-name> --scenario reasoning
./bench.py --url http://localhost:8000 --model <served-name> --scenario longctx
```

Standard library only, no dependencies. Targets any OpenAI-compatible
`/v1/chat/completions`. Output is Markdown tables that go straight into a scenario
document, prefixed with a comment recording the protocol version.

## What is fixed

| Parameter | Value | Why it is pinned |
|---|---|---|
| `max_tokens` | 512 | Reasoning models spend most of the budget on thinking; at 200 the visible answer gets truncated and answers/s is inflated |
| Concurrency levels | 1, 8, 16, 32, 64, 128, 256 | Powers of two; the default series. `--levels` overrides it per run for configuration sweeps — every other parameter stays pinned, and the deviation is written into the output header. A run with overridden levels is still `v1`; state the override in the scenario's Method section |
| Measurement window | 40 s per level | Long enough to fill the batch, short enough for a full sweep |
| Warmup | 3 requests per level, discarded | The first request after start ran 21.55 s against 1.86 s afterwards |
| Token counting | `usage` fields | Stream deltas miss reasoning tokens — this was off by a factor of 5 once |
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
