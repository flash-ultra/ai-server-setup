# AI Server Setup

Measured serving configurations for large models, organised by the machine they were
measured on. Every setup here was actually run: the numbers come from load tests on
the listed hardware, and the dead ends are documented next to the working
configuration.

## Machines

| Machine | GPUs | Status |
|---|---|---|
| [`cloudscale-gpu2-512-80-4-800/`](cloudscale-gpu2-512-80-4-800/) | 4× RTX PRO 6000 Blackwell Max-Q (sm120), no NVLink | in production |

Hardware determines what runs at all — kernel support, parallelism options, context
capacity — so it is the top level here. Findings that only hold for one machine live
in that machine's README; only what carries across hardware is on this page.

## Models

Which model has been measured on which machine, and with what result.

| Model | cloudscale `GPU2-512-80-4-800` |
|---|---|
| **DeepSeek-V4-Flash-0731** | [SGLang + SM120 patchset](cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/) — 14,657 tok/s @ C=128 · full 1M context verified |

A model measured on several machines keeps one row and gains a column per machine, so
the cross-hardware comparison lives here rather than in the directory tree.

---

## Layout

```
README.md                            this file — conventions and cross-machine lessons
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

### Measure via `usage`, not stream deltas

Reasoning models can put the overwhelming majority of generated tokens into a separate
reasoning field. Counting only streamed answer text under-reported one stack's
throughput by a factor of 5. Requests per second and TTFT are unaffected by this and
make the safer cross-stack comparison.

### Vendor tuning advice is often measured on a different shape

Recommendations from single-GPU or CPU-offload setups can invert on a multi-GPU box
with everything in VRAM, and settings that look best at empty context can lose at
realistic depth. Re-measure at the depth and concurrency you actually run.

---

## Method

Each scenario is measured with the same load test unless the scenario file says
otherwise: a prompt of roughly 1000 tokens, fixed `max_tokens`, 40 seconds per
concurrency level, GPU utilisation sampled per card throughout. Token counts come from
the `usage` fields, not from stream deltas. Reported figures are single-machine,
single-workload-shape measurements — a starting point, not a specification.

Where a claim contradicts widely repeated advice, the measurement that disproves it is
included rather than just the conclusion.
