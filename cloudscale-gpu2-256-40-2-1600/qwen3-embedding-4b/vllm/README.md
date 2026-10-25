# vLLM 0.28.0 — Qwen3-Embedding-4B beside a 320k chat model

Second container on the same two cards, stock upstream image. The configuration differs
from [the 8 B one](../../qwen3-embedding-8b/vllm/README.md) only in the model and the
memory fraction — and the memory fraction took four attempts to get right.

## Configuration in effect

```
serve --model /model --served-model-name cyberlink-embed
  --host 127.0.0.1 --port 8002
  --runner pooling
  --tensor-parallel-size 2 --trust-remote-code
  --gpu-memory-utilization 0.060 --max-model-len 8192
```

| | |
|---|---|
| VRAM | 6,520 MiB per card |
| Combined with the chat model | 94,829 of 97,887 MiB per card |
| Image | `vllm/vllm-openai:v0.28.0`, pinned |
| Restart | `cyberlink-embed.service`, started **before** the chat model |

## Pinned values

| Setting | Value | What happens if you deviate |
|---|---|---|
| `--gpu-memory-utilization` | **0.060** | the window is narrow at both ends. Below ~0.056 the engine aborts with `0.56 GiB KV cache is needed, which is larger than the available KV cache memory (0.51 GiB)`; above ~0.065 the **chat model** then fails its own check, because the fraction is of the whole card and the two budgets have to sum below 1.0 |
| `--runner pooling` | required | `--task embed` no longer exists in 0.28 and the engine exits on an unrecognised argument |
| `--max-model-len` | 8192 | the KV requirement scales with it — 0.56 GiB at 8192 against a budget that holds roughly twice that. 16384 does not fit |
| Start order | **before the chat model** | see below |
| Image tag | `v0.28.0`, not `latest` | `latest` pulled a build that failed here, and with `--rm` the container removed itself before its log could be read |

## What the memory arithmetic actually is

The engine prints what it needs; reading that is faster than inferring it from
`nvidia-smi`. Measured on this model at TP=2:

| | MiB per card |
|---|---|
| Weights, overhead and activation peak | 4,862 |
| KV for 8192 tokens | 573 |
| **Minimum budget** | **5,435** |
| At `0.060` the budget is | 5,873 |

**The fraction is of the whole card, not of what is free.** `0.95` beside a model
already holding 90 % does not mean "95 % of the remainder" — it means 90 GiB, and the
engine aborts out of memory while the card looks half empty. Size it as
`wanted_MiB / 97,887`.

## Start order is part of the configuration

Both services size themselves as a fraction of the whole card, and on this machine the
two fractions sum above 1.0 if either is generous. What decides the outcome is who
allocates first — which makes the order a pinned value rather than an implementation
detail.

Measured, same configuration, started twice in different orders:

| | starts first | starts second |
|---|---|---|
| Embedding at `0.088` | **9,213 MiB** | 6,265 MiB |

**The difference is the allocator, not the model.** vLLM reserves toward its budget
when the memory is there and simply takes less when it is not — so a footprint measured
as the second service is a leftover, not a requirement, and sizing the other service
from it produces a configuration that only works in one order.

The chat model's check is the tighter of the two: it needs 87.37 GiB free at
`--gpu-memory-utilization 0.92` and failed by **0.05 GiB** when the embedding was given
`0.062`. Both were lowered — the embedding to `0.060` and the chat to `0.905` — which
leaves 2.2 GiB of margin on the check that matters and changes neither the served
window nor the output dimension, because the chat's KV is pinned by an explicit
`--kv-cache-memory` rather than by its fraction.

## Routing

Both services sit behind one port, because the gateway expects a single upstream.
`api-router.py` dispatches on the request path — anything containing `/embeddings` goes
to 8002, everything else to 8001 — and injects the chat upstream's bearer token from
`~/.chat-api-key`. The embedding upstream needs no key.
