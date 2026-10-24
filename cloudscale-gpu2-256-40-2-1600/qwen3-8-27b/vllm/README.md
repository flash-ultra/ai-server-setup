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

**Dense is the trade-off, and it costs a steady 0.6×.** Every token reads every weight,
so decode is bound by memory bandwidth rather than by how many experts are active.
Measured against DeepSeek-V4-Flash-0731 on these same two cards:

| | this model | DeepSeek-0731 | ratio |
|---|---|---|---|
| [Single-stream decode](scenarios/single-stream.md) | 45.3 tok/s | 75.3–75.5 | **0.60** |
| [Prefill at 64k](scenarios/long-context.md) | 5131 tok/s | 8227 | **0.62** |
| [Prefill at 128k](scenarios/long-context.md) | 4343 tok/s | 7480 | **0.58** |
| [Prefill at 180k](scenarios/long-context.md) | 4207 tok/s | 7133 | **0.59** |

DeepSeek has ten times the parameters and is consistently faster, in both the
bandwidth-bound and the compute-bound phase. **Parameter count does not predict serving
speed; active parameter count does.** That the ratio is the same 0.6 in prefill and in
decode is the part worth keeping — it means the handicap is the architecture, not a
tuning gap in one phase.

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

## The reasoning text is in `reasoning`, not `reasoning_content`

With `--reasoning-parser qwen3` the separation works — `content` holds only the answer —
but vLLM 0.28 names the field **`reasoning`**. SGLang, serving DeepSeek on this same
machine, names it `reasoning_content`.

```
message keys: ['annotations', 'audio', 'content', 'function_call',
               'reasoning', 'refusal', 'role']
usage.completion_tokens_details: {"reasoning_tokens": 96}
content:   "17 × 23 = 17 × (20 + 3) = 340 + 51 = **391**"
reasoning: <96 tokens of working>
```

**This breaks the documented way of checking whether thinking is on.** Both the `v1` and
`q1` protocols say to compare `reasoning_content` between two requests; against this
engine that field is absent in *both* arms, so the check reports "no difference" and the
thinking-off row looks verified when nothing was verified. The protocol
[now says to use `usage` instead](../../../benchmark/README.md#what-is-fixed), which
both engines report.

A client written against SGLang and pointed at this engine sees no thinking at all and
no error — the same silent-acceptance failure mode as the
[switch keys above](#thinking-is-on-by-default-and-two-of-four-switches-work), one layer
further out.

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
| [single-stream](scenarios/single-stream.md) | measured — `v1`, both arms |
| [concurrent-load](scenarios/concurrent-load.md) | measured — `v1`, both arms, full ladder |
| [long-context](scenarios/long-context.md) | measured — `v1`, four depths to 240k, 3/3 needles each |
| [reasoning-cost](scenarios/reasoning-cost.md) | measured — `v1`, three variants at C=8 and 32 |
| [quality](scenarios/quality.md) | measured — `q1`, both arms |

**The only setup in this repository with a complete series under both protocols.**
