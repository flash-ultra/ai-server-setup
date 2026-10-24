# Qwen3.8-27B

The dense 27 B release at **BF16** on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Set up and measured 2026-10-23.

| | |
|---|---|
| Checkpoint | [`Qwen/Qwen3.8-27B`](https://huggingface.co/Qwen/Qwen3.8-27B) |
| Size on disk | 51.8 GiB |
| Architecture | `Qwen3_5ForConditionalGeneration`, 64 layers, **dense** |
| Quantisation | **none** — BF16 |
| Native context | 262,144 · **262,144 served here** |
| Modality | text **and images**, native vision tower |

## Verdict

**The best answers measured on this machine, with no throughput measurement to set
against them.** Both halves of that sentence matter.

On quality it beats [DeepSeek-V4-Flash-0731](../deepseek-v4-flash-0731/) — 284 B against
27 B, on the same cards, same protocol, same day — in **four of five benchmarks with
thinking on**, and loses four of five with thinking off — in both cases by margins too
small for 200 samples to establish, which is itself the point. It is also the first model here
that needs no quantisation, sees images without a second container, and leaves enough
room on the two cards for an embedding model beside it.

| Protocol [`q1`](vllm/scenarios/quality.md), thinking **on** | this model | DeepSeek-0731 |
|---|---|---|
| HumanEval | **0.982** | 0.963 |
| IFEval `prompt_strict` | **0.920** | 0.895 |
| IFEval `inst_strict` | **0.943** | 0.928 |
| GSM8K | **0.990** | 0.970 |
| MMLU-Pro | 0.850 | **0.870** |

**None of those five margins clears twice the standard error of the difference**, the
largest being 2.5 points against a resolution of roughly 5. The table says "not
measurably behind a model ten times its size", which is the finding — not "ahead". The
one result here that does clear its error bar by a wide margin is the arm comparison
*within* this model: thinking is worth **+13.5 points** on IFEval `prompt_strict`, far
more than it buys anywhere else.

**What is missing is the other half of the decision.** Not one level of the `v1` ladder
has been run against this setup — no single-stream figure, no concurrency sweep, no
long-context test, no needles. Dense at BF16 reads 25.9 GiB of weights per card for
every token, so it is expected to be slower per token than the sparse models in the
machine table; by how much is **unmeasured**, and a number read off the engine log during
a quality run is not a substitute. Until `bench.py` has run, this model is absent from
every throughput table in this repository on purpose.

## What it changes operationally

**Images stop being an architecture problem.** On this machine, serving images alongside
DeepSeek-0731 needed a separate llama.cpp container, a persistent image store and an MCP
tool, because [nothing fits beside that checkpoint](../README.md#two-cards-set-a-hard-ceiling-on-model-size).
Here the vision tower is in the weights that load anyway.

**A second model fits.** [`Qwen3-Embedding-8B`](../qwen3-embedding-8b/) runs on the same two cards at
`--gpu-memory-utilization 0.14` while this one holds `0.82`, 95,230 of 97,887 MiB per
card in total. That cost three points of utilisation and 91,482 tokens of KV pool — the
details are in the [setup README](vllm/README.md#configuration-in-effect).

**The thinking switch is inverted relative to DeepSeek.** Thinking is **on** by default
here and off by default there, and the key that works on one is silently ignored by the
other. A gateway alias copied across does not fail; it serves the wrong arm.

## Setups

| Setup | Status |
|---|---|
| [vLLM 0.28.0, unpatched](vllm/) | in production — quality measured, throughput not |

## Scenario coverage

| Scenario | vLLM TP=2 |
|---|---|
| [quality](vllm/scenarios/quality.md) | measured, both arms |
| `single-stream` | **not measured** |
| `concurrent-load` | **not measured** |
| `long-context` | **not measured** |

## Open questions that would change a decision

Owned one level down, in [`vllm/README.md`](vllm/README.md#still-open) — summarised here,
not duplicated:

- **The whole `v1` series.** Without it this model cannot be ranked against anything in
  the machine table, and the trade it offers — better answers, dense decode — is half
  unquantified.
- **Single-card operation**, which no other large model here can do. It would free a
  whole card and change the machine's capacity plan.
- **Vision quality.** Native images are a main argument for this model and nothing was
  benchmarked.

### Not planned

- **A quantised variant.** It fits at BF16 with 14 GiB per card to spare, so quantisation
  would trade measurable quality for headroom nothing currently needs. Revisit only if a
  third service has to fit.
- **Comparison against the `trials/` numbers.** Different protocol, by the rule that
  [applies to that directory](../trials/README.md).
