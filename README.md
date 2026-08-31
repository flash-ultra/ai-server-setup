# AI Server Setup

Measured serving configurations for large models, organised by the machine they were
measured on. Every setup here was actually run: the numbers come from load tests on
the listed hardware, and the dead ends are documented next to the working
configuration.

## Machines

| Machine | GPUs | Status |
|---|---|---|
| [`cloudscale-gpu2-256-40-2-1600/`](cloudscale-gpu2-256-40-2-1600/) | 2× RTX PRO 6000 Blackwell Max-Q (sm120), no NVLink | current |
| [`cloudscale-gpu2-512-80-4-800/`](cloudscale-gpu2-512-80-4-800/) | 4× RTX PRO 6000 Blackwell Max-Q (sm120), no NVLink | superseded |

Hardware determines what runs at all — kernel support, parallelism options, context
capacity — so it is the top level here. Findings that only hold for one machine live
in that machine's README; only what carries across hardware is on this page.

## Models

Which model has been measured on which machine, and with what result.

| Model | cloudscale `GPU2-512-80-4-800` | cloudscale `GPU2-256-40-2-1600` |
|---|---|---|
| **MiniMax-M2.5-NVFP4** · 116 B, 8/256 experts, 2 cards | — | [vLLM 0.28.0, unpatched](cloudscale-gpu2-256-40-2-1600/minimax-m2-5/) — 9.65–9.75 answers/s over two runs · monotone ladder · 100 % on both cards |
| **Qwen3.8-Flash-Next** · 512 experts, 10 active, 2 cards | — | [llama.cpp master](cloudscale-gpu2-256-40-2-1600/qwen3-8-flash-next/) — 6.83–6.85 answers/s · **images** · pinned at 45 % GPU by the layer split |
| **DeepSeek-V4-Flash-0731** · 284 B | [SGLang + SM120 patchset](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/), 4 cards — 19.65 req/s peak · full 1M context verified | [same image at TP=2](cloudscale-gpu2-256-40-2-1600/deepseek-v4-flash-0731/), 2 cards — 32.58–32.65 answers/s, thinking off by default · spread ≤ 5 % |
| **DeepSeek-V4-Flash-NVFP4** · 2 cards, [different release](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/README.md#what-this-is-not-comparable-to) | [vLLM B12X SM120 kit](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/) — 9.97 answers/s · 159–163 tok/s decode with MTP · non-monotone under load | — |
| **Gemma-4-26B-A4B** · sparse, 1 card | [llama.cpp · SGLang · vLLM](cloudscale-gpu2-512-80-4-800/gemma-4-26b-a4b/) — 31.88 answers/s · [vLLM 5.9× llama.cpp under load](cloudscale-gpu2-512-80-4-800/gemma-4-26b-a4b/engine-comparison.md) | — |
| **Gemma-4-31B** · dense, 1 card | [llama.cpp](cloudscale-gpu2-512-80-4-800/gemma-4-31b/) — 0.80 answers/s · stalls past 8 concurrent | — |
| **Muse-Glimmer-30B** · dense, 1 card | [llama.cpp](cloudscale-gpu2-512-80-4-800/muse-glimmer-30b/) — 1.27 answers/s · only engine that knows the architecture | — |

A model measured on several machines keeps one row and gains a column per machine, so
the cross-hardware comparison lives here rather than in the directory tree.

**The peak column is a pointer, not a ranking.** These rows do not share a workload: the
DeepSeek and the two llama.cpp-only rows ran with thinking on, the Gemma-4-26B-A4B row
with thinking off — worth a factor of 3.4 by itself — and the rows serve one, two or four
GPUs. The two DeepSeek rows are different model releases rather than two setups of one
model, so they are not each other's baseline either. Follow the link before comparing two
numbers here.

---

## Layout

```
README.md                            this file — conventions and cross-machine lessons
benchmark/
  README.md                          measurement protocol — read before measuring
  bench.py                           the tool every number comes from
<machine>/
  README.md                          hardware spec, machine-level findings, model index
  <model>/
    README.md                        model summary, verdict, scenario coverage
    <server-setup>/
      README.md                      engine, configuration, pinned values
      scenarios/
        <scenario>.md                one workload shape: method and measurements
```

**Machine** — one physical or virtual host in one configuration. The directory name is
the provider's flavour name where there is one, so it can be ordered again.

**Server setup** — one serving stack for one model on that machine: engine, build,
container and configuration together. Two forks of the same engine are two setups if
their configuration differs in ways that change the numbers.

**Scenario** — one workload shape measured against a setup. Slugs are kept identical
across setups and machines so the numbers stay comparable:

| Slug | Workload |
|---|---|
| `single-stream.md` | one request at a time — interactive single user |
| `concurrent-load.md` | concurrency sweep — throughput and latency under parallel load |
| `long-context.md` | behaviour as context depth grows |

A scenario file exists only where the measurement was actually run — no placeholder
files for workloads nobody has measured.

**Open items are owned by the lowest level where the work would happen.** A scenario
file lists the measurements missing for its workload shape, a setup README lists
configuration and correctness gaps, and the model README carries a linked rollup of
the questions that would change a decision instead of a second copy. Anything
deliberately dropped is marked as not planned, with the reason — so that an empty
spot means "nobody has looked", never "we forgot to write it down".

---

## What carries across machines

### Tensor parallelism depends on the model's attention layout

Models using MLA with a single KV head cannot have their KV cache split across cards.
Engines that only offer layer-splitting will then use the GPUs sequentially — you get
memory capacity, not combined compute. Check `num_key_value_heads` in the checkpoint
config before assuming multi-GPU scaling.

### Recent architectures need a patched fork or a community image

Kernel support lags the checkpoints, and the gap is architecture-specific rather than
vendor-wide. Establish that a forward pass completes on your compute capability before
planning capacity around a model.

Support is also engine-version-specific, and cheap to check **before** downloading tens
of gigabytes — every engine keeps a registry you can read:

```bash
# llama.cpp — the architecture table in the source
docker run --rm --entrypoint sh <image> -c "grep -oE '\"[a-z0-9-]+\"' /src/src/llama-arch.cpp"

# vLLM
docker run --rm --entrypoint python3 <image> -c \
  "from vllm.model_executor.models import ModelRegistry; print(ModelRegistry.get_supported_archs())"

# SGLang — one module per architecture
docker run --rm --entrypoint python3 <image> -c \
  "import sglang.srt.models as m, pkgutil; print([x.name for x in pkgutil.iter_modules(m.__path__)])"
```

**Match on the architecture, not on the model's name.** The registry keys are
architecture identifiers, and release names drift away from them: `Qwen3.8-27B` declares
`architectures: ["Qwen3_5ForConditionalGeneration"]`, so every engine that already ran
Qwen3.5 runs it unchanged — while a search for "qwen3.8" in the same registries returns
nothing and reads as "unsupported". Read `config.json` from the checkpoint first:

```bash
curl -sL https://huggingface.co/<repo>/resolve/main/config.json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['architectures'], d.get('model_type'))"
```

Checked this way, four models took minutes rather than the hours their downloads would
have cost — and one of the four was nearly dropped on a name mismatch alone.

**When fetching weights, repeat the flag rather than the value.**
`hf download REPO --include "A/*" "B/*"` reads `B/*` as an explicit filename, drops the
pattern, and emits a warning that scrolls past in the progress output — you end up with
whatever `B` matched and none of `A`. Write `--include "A/*" --include "B/*"`.

### Switches that a model does not know are accepted, not rejected

Request options that ride in `chat_template_kwargs` are rendered by the checkpoint's own
Jinja template. A key the template never reads is not an error — the request succeeds
and the option does nothing. Three models measured here take three different answers to
"turn thinking off": `thinking`, `enable_thinking`, and one whose template has no switch
at all.

The failure mode is a measurement that looks like a result: the thinking-off arm matches
the thinking-on arm, and the honest-looking conclusion is "it makes no difference". Check
the effect before trusting the row — one request each way, compare `reasoning_content`.
The same applies to any proxy in the path: a gateway with `drop_params` enabled will
remove unknown options before the model ever sees them.

### Measure via `usage`, not stream deltas

Reasoning models can put the overwhelming majority of generated tokens into a separate
reasoning field. Counting only streamed answer text under-reported one stack's
throughput by a factor of 5. Requests per second and TTFT are unaffected by this and
make the safer cross-stack comparison.

### Vendor tuning advice is often measured on a different shape

Recommendations from single-GPU or CPU-offload setups can invert on a multi-GPU box
with everything in VRAM, and settings that look best at empty context can lose at
realistic depth. Re-measure at the depth and concurrency you actually run.

### A published configuration can be verified and still fail under load

Community kits for unsupported architectures are how these models run at all, and their
numbers are usually honest about *what* they measured. Read that scope literally. One kit
here documents a long-context configuration as "capacity-verified; load-tested only on
short prompts" — and it is exactly true: it serves a single long request and
[kills the engine at 16 concurrent ones](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/vllm-b12x/README.md#pinned-values),
because a kernel workspace is sized once at startup from a scheduling flag. Single-stream
numbers reproduced to within a few percent on the same kit.

Two habits follow. Re-run the concurrency ladder yourself before adopting any published
configuration, however well documented. And check how the process dies: this one exits
with **status 0** and returns HTTP 500 afterwards, so `docker ps` reads like a clean
shutdown and only the log names the cause.

---

## Method

All numbers come from [`benchmark/bench.py`](benchmark/README.md), which pins every
parameter that affects throughput: prompt text, concurrency levels, `max_tokens`,
measurement window, warmup, and how tokens are counted. That is what makes series
comparable across engines, models and machines.

```bash
./benchmark/bench.py --url http://localhost:8000 --model <name> --scenario concurrent
```

Token counts come from the `usage` fields, never from stream deltas — on a reasoning
model that difference was once a factor of 5. Reported figures are single-machine,
single-workload-shape measurements: a starting point, not a specification.

The DeepSeek-V4-Flash-0731 series predates the protocol and deviates from it in
documented ways; see [known deviations](benchmark/README.md#known-deviations-in-existing-documents)
before placing its tables side by side.

Where a claim contradicts widely repeated advice, the measurement that disproves it is
included rather than just the conclusion.
