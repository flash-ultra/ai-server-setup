# vLLM 0.28.0 — NVFP4 on two cards

Stock `vllm/vllm-openai:v0.28.0`, no patches, on
[cloudscale `GPU2-256-40-2-1600`](../../README.md). Tested 2026-08-30.

| | |
|---|---|
| Engine | vLLM 0.28.0 |
| Image | `vllm/vllm-openai:v0.28.0` — unmodified upstream |
| Checkpoint | [`nvidia/MiniMax-M2.5-NVFP4`](https://huggingface.co/nvidia/MiniMax-M2.5-NVFP4) — 130.3 GiB |
| Cards | 2 of 2 (TP=2) |
| Context served | 196,608 |
| KV cache | 395,376 tokens · max concurrency 2.01× at full context |
| Memory in use | 92,307 MiB per card of 97,887 |
| Time to `/health` 200 | ~3 minutes |

## Configuration in effect

```
--model /model --served-model-name cyberlink
--host 127.0.0.1 --port 8000
--tensor-parallel-size 2
--gpu-memory-utilization 0.93
--max-model-len 196608
--max-num-seqs 32
--enable-auto-tool-choice --tool-call-parser minimax_m2
--reasoning-parser minimax_m2
```

Nothing else is set. No speculation, no quantised KV cache, no compilation flags —
the defaults of the release.

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| `--tool-call-parser` | `minimax_m2` | without it **and** `--enable-auto-tool-choice`, every request carrying `tool_choice` is rejected before the model sees it: `"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set` |
| `--max-model-len` | `196608` | the checkpoint's `max_position_embeddings`; higher is refused at start |
| `--gpu-memory-utilization` | `0.93` | 65.2 GiB of weights per card leaves room; this is not a tight fit |

## Thinking cannot be switched off, and that is measured

Four candidate switches, same question, `reasoning_tokens` from `usage`:

| Variant | reasoning tokens |
|---|---|
| default | 213 |
| `chat_template_kwargs: {"enable_thinking": false}` | 369 |
| `chat_template_kwargs: {"thinking": false}` | 152 |
| `reasoning_effort: "none"` | 176 |

**None reaches zero.** All four requests succeed, none logs a warning, and the
checkpoint's template carries no switch the engine can reach. Every figure for this
setup is therefore a thinking-on figure, and it cannot be put beside another model's
thinking-off row.

The keys that do work elsewhere on this machine are listed at
[repository level](../../../README.md#switches-that-a-model-does-not-know-are-accepted-not-rejected) —
this is the case where the answer is "there is none", which only a probe distinguishes
from "the key was wrong".

## Scenarios

| Scenario | Status |
|---|---|
| [single stream](scenarios/single-stream.md) | measured |
| [concurrent load](scenarios/concurrent-load.md) | measured |
| [long context](scenarios/long-context.md) | measured, with a harness correction |
| reasoning cost | **not measured** — no key disables thinking, [why](../README.md#model-specific-gotchas) |
