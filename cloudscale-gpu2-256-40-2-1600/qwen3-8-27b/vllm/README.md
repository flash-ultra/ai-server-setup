# vLLM 0.28.0, unpatched — Qwen3.8-27B on two cards

Stock upstream image, no fork, no patchset. Set up and measured 2026-10-23.

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.28.0` |
| Checkpoint | [`Qwen/Qwen3.8-27B`](https://huggingface.co/Qwen/Qwen3.8-27B) — 51.8 GiB, **BF16** |
| Architecture | `Qwen3_5ForConditionalGeneration` — **dense**, no MoE |
| Layers / hidden / KV heads | 64 / 5120 / 4 |
| Cards | 2 of 2 (TP=2) |
| Modality | text **and images** — native vision tower, no second service |
| Context served | **262,144** |

## Configuration in effect

```
serve --model /model --served-model-name cyberlink
  --host 127.0.0.1 --port 8001
  --tensor-parallel-size 2 --trust-remote-code
  --gpu-memory-utilization 0.82 --max-model-len 262144
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder --enable-auto-tool-choice
```

| at `0.82` (running now) | |
|---|---|
| VRAM per card | 81,042 of 97,887 MiB |
| Available KV cache | 47.17 GiB |
| KV pool | 1,515,207 tokens |
| Full-length requests in parallel | 5.78 at 262,144 each |

**`0.82` is not the model's requirement, it is the room left for a neighbour.** The
[quality measurement](scenarios/quality.md) ran at `0.85` — 50.01 GiB of KV,
1,606,689 tokens, 6.13 full-length requests. The three points were given up to fit
`Qwen3-Embedding-8B` on the same two cards at `0.14`, which takes 14,104 MiB each and
leaves 95,230 of 97,887 MiB in use. Serving this model alone, `0.90` is unproblematic.

## Pinned values

| Setting | Value | What happens if you deviate |
|---|---|---|
| `--reasoning-parser` | **`qwen3`** | the thinking text lands **in `content`** instead of in `reasoning_content`. A grader then scores the scratchpad as the answer, and the model looks far worse than it is |
| `--tool-call-parser` | **`qwen3_coder`** | `hermes` is accepted, logs nothing, and delivers tool calls as raw text `<tool_call><function=…>` in `content` instead of a structured `tool_calls` array. Every gateway with tools registered then fails, and the engine never complains |
| `--enable-auto-tool-choice` | set | any request carrying `tool_choice: auto` is rejected with HTTP 400 — which is every request from a gateway that has tools registered |
| `--max-model-len` | 262,144 | the native window. A gateway in front must be told `window − output budget`, not the window, or it answers 400 `ContextWindowExceeded` before the engine sees the request |
| thinking switch | **`enable_thinking`** or `reasoning_effort` | thinking is **on by default**. `thinking: false` — the correct key for DeepSeek on this same machine — is silently ignored |

## BF16 on two cards, and what dense costs

This is the first model in this repository served at **full precision**: 25.9 GiB of
weights per card against 95.6 GiB available. No quantisation, so no question about what
the quantisation cost.

**Dense is the trade-off.** Every token reads every weight, so decode is bound by memory
bandwidth rather than by how many experts are active:

| | weights read per token |
|---|---|
| this model, BF16, TP=2 | 25.9 GiB per card |
| DeepSeek-V4-Flash-0731, 6 of 256 experts | a fraction of 284 B |

DeepSeek is ten times the parameter count and faster per token. Size and decode speed
point in opposite directions here. **How much faster is not measured** — see
[Still open](#still-open).

## Thinking is on by default, and two of four switches work

Same question, four variants, completion tokens counted via `usage`:

| Variant | completion tokens | thinking |
|---|---|---|
| default, nothing set | 66 | **on** |
| `chat_template_kwargs: {"enable_thinking": false}` | **4** | off |
| `reasoning_effort: "none"` | **4** | off |
| `reasoning_effort: "low"` | 56 | on |
| `chat_template_kwargs: {"thinking": false}` | 80 | **no effect** |

**The direction is the opposite of DeepSeek-V4-Flash-0731 on the same machine**, where
thinking is off by default and `reasoning_effort: low` turns it **on**. A gateway alias
copied from one model to the other does the wrong thing silently: no error, no warning,
just the other arm. This is the third distinct answer to "turn thinking off" measured on
this machine — see the
[repository-level note](../../../README.md#switches-that-a-model-does-not-know-are-accepted-not-rejected).

## Images need no second service

The checkpoint carries its own vision tower, and vLLM loads it with the rest of the
model. A base64 image in an `image_url` content part is described correctly with no
configuration beyond the command line above.

**That retires a whole construction.** Serving images alongside DeepSeek-0731 on this
machine required a separate llama.cpp container, an image store and an MCP tool, because
[nothing fits beside that checkpoint](../../README.md#two-cards-set-a-hard-ceiling-on-model-size).
Here the capability is in the weights that were loaded anyway.

**What the images cost in quality is not measured** — `mmmu` and `mathvista` ship with
`inspect_evals` and were not run.

## Scenarios

| Scenario | Status |
|---|---|
| [quality](scenarios/quality.md) | measured — protocol `q1`, both thinking arms |
| `single-stream` | **not measured** |
| `concurrent-load` | **not measured** |
| `long-context` | **not measured** |

## Still open

- **No `v1` throughput series exists for this setup.** Not one level of the ladder was
  run. The figure of ~47 output tok/s that appears in operational notes was read off the
  engine's own log line during a single-stream quality run; it is not a `v1` number, it
  has no concurrency level attached, and it must not be placed in the machine or
  repository tables. Until `bench.py` has run, this model has no throughput result.
- **Single-card operation.** 51.8 GiB of weights fit on one 95.6 GiB card, which no other
  large model here manages. What that costs in tokens per second, and what the freed card
  could then host, is unmeasured — and it is the question that would change the machine's
  capacity plan.
- **Vision quality.** It answers correctly on an ad-hoc test image. No benchmark was run.
- **Context above the measured depth.** 262,144 is configured and the KV arithmetic
  allows 5.78 full-length requests in parallel. No needle test was run at any depth.
