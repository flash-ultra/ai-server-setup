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
| **Qwen3.8-27B** · dense **BF16**, 2 cards | — | [vLLM 0.28.0, unpatched](cloudscale-gpu2-256-40-2-1600/qwen3-8-27b/) — thinking **on**: **1,821 output tok/s** @ C=256, 9.43 answers/s at 193 tokens · thinking **off**: **718 tok/s**, 13.45 answers/s at 53 tokens · 3/3 needles to **240k**, the deepest here · **0.6× DeepSeek on prefill**; decode 49.5 tok/s, both arms · best quality measured under [`q1`](benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai) · **images**, native · full precision |
| **MiMo-V2.6-Flash-RL** · FP8, 2 cards | — | [vLLM, vendor image](cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/) — **3,129 output tok/s** @ C=256 · **46.05 answers/s** at p50 5.74 s · thinking **on** · **images** · 100 % on both cards at every level · 196,608 context, 3/3 needles at 180k |
| **MiniMax-M2.5-NVFP4** · 116 B, 8/256 experts, 2 cards | — | [vLLM 0.28.0, unpatched](cloudscale-gpu2-256-40-2-1600/minimax-m2-5/) — **2,947–3,126 output tok/s** @ C=256 · 9.65–9.75 answers/s · decode 116.6 · **thinking cannot be switched off**, probed not assumed · quality under [`q1`](benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai): last of three in three benchmarks, behind a 27 B dense model in all five |
| **Qwen3.8-Flash-Next** · 512 experts, 10 active, 2 cards | — | [llama.cpp master, Q6 on 6 slots](cloudscale-gpu2-256-40-2-1600/qwen3-8-flash-next/) — **1,390 output tok/s** @ C=256 · 7.47 answers/s · **images** · pinned in the forties by the layer split |
| **DeepSeek-V4-Flash-0731** · 284 B | [SGLang + SM120 patchset](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/), 4 cards — **6,454 output tok/s** @ C=768 · 19.65 req/s · full 1M context verified | [same image at TP=2](cloudscale-gpu2-256-40-2-1600/deepseek-v4-flash-0731/), 2 cards — thinking **off**: **1,159–1,183 output tok/s** @ C=256, 32.10–32.65 answers/s at 35 tokens · thinking **on**: **3,584 tok/s**, 10.97 answers/s at 327 tokens · extended to C=512: **1,436.5 tok/s** and still climbing · spread ≤ 5 % |
| **DeepSeek-V4-Flash-NVFP4** · 2 cards, [different release](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/README.md#what-this-is-not-comparable-to) | [vLLM B12X SM120 kit](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-nvfp4/) — **404 output tok/s** @ C=256 · 9.97 answers/s · 159–163 tok/s decode with MTP · non-monotone under load | — |
| **Gemma-4-26B-A4B** · sparse, 1 card | [llama.cpp · SGLang · vLLM](cloudscale-gpu2-512-80-4-800/gemma-4-26b-a4b/) — 31.88 answers/s @ C=32 (vLLM; **token throughput under load not recorded** for that engine) · [vLLM 5.9× llama.cpp under load](cloudscale-gpu2-512-80-4-800/gemma-4-26b-a4b/engine-comparison.md) | — |
| **Gemma-4-31B** · dense, 1 card | [llama.cpp](cloudscale-gpu2-512-80-4-800/gemma-4-31b/) — **310 output tok/s** @ C=32 · 0.80 answers/s · stalls past 8 concurrent | — |
| **Muse-Glimmer-30B** · dense, 1 card | [llama.cpp](cloudscale-gpu2-512-80-4-800/muse-glimmer-30b/) — **521 output tok/s** @ C=32 · 1.27 answers/s · only engine that knows the architecture | — |

A model measured on several machines keeps one row and gains a column per machine, so
the cross-hardware comparison lives here rather than in the directory tree.

**Three models on the two-card machine now carry both a `v1` and a `q1` series, and the
two protocols order them in reverse.** Qwen3.8-27B has the best answers and the slowest
decode; MiniMax decodes 2.4× faster and comes last in three of five benchmarks. Across
those three — 27 B dense, 116 B MoE, 284 B MoE — **parameter count buys nothing
measurable in quality**: only one margin in the whole comparison clears two standard
errors. It does cost a factor of 2.4 in decode speed.

**The peak column is a pointer, not a ranking.** These rows do not share a workload: the
DeepSeek and the two llama.cpp-only rows ran with thinking on, the Gemma-4-26B-A4B row
with thinking off — worth a factor of 3.4 by itself — and the rows serve one, two or four
GPUs. The context served differs too, and a smaller window leaves more room for the
batch — though on the one row where that was tested, quadrupling the window changed
throughput by 0.1 %. The two DeepSeek rows are different model releases rather than two setups of one
model, so they are not each other's baseline either. Follow the link before comparing two
numbers here.

**Output tokens per second is quoted first because it is what the field reports**, and
because answers per second is not comparable across these rows: tokens per answer spans
35 to 327 here, a factor of nine, driven by thinking state rather than by speed.

**The thinking state moves a row further than the hardware does.** DeepSeek-V4-Flash-0731
on two cards, measured both ways on the same day, spans 1,173 to 3,584 output tokens per
second — a 3.1× range from one request parameter. That is wider than the gap between any
two models in this table. A figure without a stated thinking arm is not comparable to
anything, and neither column is wrong; they measure different work.

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

**The architecture string tells you whether the model loads, not which implementation
loads it.** MiMo-V2.6-Flash declares `MiMoV2ForCausalLM`, which in vLLM's registry is a
text-only class; the engine resolves the multimodal `MiMoV2OmniForCausalLM` instead,
evidently from the `vision_config` and `audio_config` sitting in the same `config.json`.
The difference is not cosmetic — the multimodal class loads encoders that take GiB out of
the KV budget. The registry check is still the right first step; the startup log is where
the question is actually settled.

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

The sharpest case measured here is
[MiMo-V2.6-Flash](cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/vllm/README.md#thinking-can-be-switched-off-and-only-two-of-five-ways-work):
five plausible candidate keys, **two** that work and **three** that return a normal answer
with thinking still on — including `thinking`, which is the correct key for a different
model on the same machine. Switching it off is worth 43 % more answers per second there,
so the false negative would have cost a real result.

**The same applies one level down, to engine flags.** `--kv-cache-dtype fp8` on that
setup is accepted, logs nothing unusual, and leaves the cache arithmetic
[identical to the digit](cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/vllm/README.md#--kv-cache-dtype-fp8-is-accepted-and-does-nothing):
3.18 GiB needed at 131,072 either way, same max-length estimate. A flag that should halve
the cache and does not is invisible unless you read the engine's own KV figures before and
after.
The same applies to any proxy in the path: a gateway with `drop_params` enabled will
remove unknown options before the model ever sees them.

### A serving ceiling can be an engine default rather than a hardware limit

One setup here served 49,152 tokens of context and failed to start at anything larger,
with the engine reporting 2.36 GiB of KV cache available and estimating 54,528 as the
longest workable window. The weights left 12.8 GiB per card unaccounted for, so the
arithmetic looked like a hardware wall.

It was a profiling default. vLLM's CUDA-graph memory estimator was reserving the
difference and saying so in a line that reads like an informational note:
`--gpu-memory-utilization=0.9700 is equivalent to 0.9637 without CUDA graph memory
profiling`. Disabling it and raising utilisation by one point:

| | before | after |
|---|---|---|
| Available KV | 2.36 GiB | 3.9 GiB |
| Longest window the engine would start | 54,528 | 198,208 |
| Served | 49,152 | **196,608** |
| Answers/s at concurrency 256 | 46.10 | 46.05 |

**Four times the context at unchanged throughput.** The full before/after is in the
[setup README](cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/vllm/README.md#a-cuda-graph-profiling-default-costs-three-quarters-of-the-context-window).

Two things generalise. **A "model does not fit" conclusion drawn from a first boot is a
statement about the engine's defaults as much as about the model** — read the startup log
for what is being reserved before sizing hardware around the result. And **the KV figure
an engine reports is not a constant of the checkpoint**: it moved by 65 % here without
touching weights, quantisation or cards.

### The protocol ladder stops at 256, and models do not

Concurrency 256 is where `v1` ends, not where a machine ends. Extended to 512, one setup
here gained 22 % in answers per second and 24 % in tokens per second over its own 256
figure, at 98 % GPU and with the curve still rising. Every peak in this repository is
therefore "the best measured inside the protocol", and for a capacity decision the ladder
has to be pushed until it turns over.

### A KV pool does not scale linearly, so do not extrapolate its size

Sizing a large context budget from a measurement at a small one overestimates what it
costs, and the error can be large enough to change a hardware decision.

On Qwen3.8-Flash-Next the first 229,376 tokens of pool cost 0.0266 MiB each and the next
786,432 cost 0.0164 — a projection from the first pair put the larger pool 14 % above
what it actually used.

On MiMo-V2.6-Flash the same effect is a factor of two. The same setup, two window sizes:

| | 49,152 window | 196,608 window |
|---|---|---|
| KV pool | 135,191 tokens | 197,494 tokens |
| Bytes per token | 49.1 KiB | **25.4 KiB** |

**The pool got 46 % larger on 38 % less memory.** Hybrid attention explains it: some
layers carry a sliding window whose cost saturates once the context exceeds its width,
while the rest keep growing. Below that width every layer stores in full — so a
short-window measurement is the expensive regime, not the cheap one. The same signature
shows in that engine's failure messages: 3.18 GiB needed at 131,072 but 4.59 GiB at
262,144, where a linear cache would want 6.36.

Measure at the size you intend to serve, or at two points that bracket it.

### More server slots lower latency without raising the ceiling

Where an engine exposes a slot count, it decides how quickly the machine reaches
saturation, not where saturation is. Measured on llama.cpp with one slot against six:
73 % more output tokens per second at eight concurrent requests, 6.8 % at 256, and
roughly half the median latency at every level from eight upward. The throughput curves
converge; the latency curves do not. If the complaint is response time under moderate
load, the slot count is the first thing to check — and it costs only KV memory.

### Active parameter count predicts prefill speed, not parameter count

Two models on the same two cards with the same driver: a **27 B dense** model at BF16
and a **284 B mixture-of-experts** at FP8 that activates 6 of 256 experts per token. The
284 B model prefills faster, by a steady factor at every depth measured:

| | 27 B dense | 284 B MoE | ratio |
|---|---|---|---|
| Prefill at 64k | 5131 tok/s | 8227 | 0.62 |
| Prefill at 128k | 4343 tok/s | 7480 | 0.58 |
| Prefill at 180k | 4207 tok/s | 7133 | 0.59 |

The dense model reads all 25.9 GiB of its per-card weights for every token; the sparse
one reads a fraction of a much larger number.

**The consequence is for capacity planning from a model card.** "27 B" reads as the
cheap option and prefills at 0.6× the 284 B alternative on the same hardware, while
needing the full precision that makes it good. Size on disk predicts whether a model
*fits*; the activation pattern predicts what it *costs* to serve.

**Decode is a separate question and only half-answered here.** Measured properly — a
streaming request, tokens after the first over `duration − TTFT` — the dense model runs
at [49.5 tok/s in both thinking arms](cloudscale-gpu2-256-40-2-1600/qwen3-8-27b/vllm/scenarios/single-stream.md#decode-rate-measured-separately).
There is no such figure for the MoE on these two cards, so the prefill ratio above must
not be read as applying to decode. **The `v1` single-stream column is not a substitute**:
it counts output tokens over a fixed window, so it folds in one prefill per answer and
understates models that answer briefly. On the one model where both were measured it
reads 45.3 where decode is 49.5, and it splits the two thinking arms (51.9 against 45.3)
where decode does not differ at all.

The same pair inverts on answer quality — see the
[machine's quality section](cloudscale-gpu2-256-40-2-1600/README.md#quality).

### A benchmark score hides why the model stopped talking

An answer cut off at the token cap is graded as a wrong answer. The run reports an
ordinary accuracy with an ordinary standard error, and nothing in the output separates
"the model was wrong" from "the model was interrupted".

Measured on one benchmark cell, one model, same day: **0.755 at a cap of 8,192 and
0.850 at 50,000**, with 38 of 200 answers truncated in the first. A second benchmark in
the same run moved 0.921 to 0.982 the same way.

Two things follow, and both cost nothing. **Read the abort reasons before using the
score** — the
[one command that does it](benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai)
is in the protocol. And **be suspicious of the direction of the error**: truncation only
ever lowers a score, so it is indistinguishable from the result you may already expect
when a small model is compared against a large one.

The same shape appears one layer out. A reply that is slower than the client's own HTTP
timeout produces retries and a run that ends with fewer samples than it was asked for —
and still prints a table. Check that the sample count matches the limit.

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

Throughput numbers come from [`benchmark/bench.py`](benchmark/README.md) under
protocol `v1`, which pins every parameter that affects them: prompt text, concurrency
levels, `max_tokens`, measurement window, warmup, and how tokens are counted. That is
what makes series comparable across engines, models and machines.

Quality is a second protocol,
[`q1`](benchmark/README.md#quality-protocol-q1-measured-with-inspect-ai), measured with
Inspect AI against the engine directly and always on **both thinking arms**. A `v1`
figure and a `q1` figure answer different questions and neither substitutes for the
other — one model here has both, the rest have one or the other, and the tables say
which.

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
