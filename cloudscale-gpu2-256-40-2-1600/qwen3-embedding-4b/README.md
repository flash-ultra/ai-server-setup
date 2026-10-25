# Qwen3-Embedding-4B

The embedding model that fits beside a 320k chat window on
[cloudscale `GPU2-256-40-2-1600`](../README.md). Set up 2026-10-25, replacing
[Qwen3-Embedding-8B](../qwen3-embedding-8b/).

| | |
|---|---|
| Checkpoint | [`Qwen/Qwen3-Embedding-4B`](https://huggingface.co/Qwen/Qwen3-Embedding-4B) |
| Output dimension | **2560** — fixed, see below |
| Max input | 8192 tokens |
| Cards | 2 of 2 (TP=2), **alongside the chat model** |
| Served as | `cyberlink-embed` on `127.0.0.1:8002` |

## Verdict

**It is the capability, not a measurement.** This directory documents a configuration
that works; there is no `v1` series and no retrieval benchmark.

It is here because the 8 B version no longer fits. Swapping the chat model to
[DeepSeek-V4.1-Flash at a 327,680-token window](../deepseek-v4-1-flash-1017/) left
about 6.5 GiB per card instead of the 14.1 GiB the 8 B used, and the embedding is the
side of that trade that had room to give.

## The dimension change is not a setting, and it broke an index

| | 8 B | 4 B |
|---|---|---|
| Output dimension | 4096 | **2560** |

2560 is the model's own hidden size, not a truncation. **It cannot be changed per
request either** — vLLM rejects the OpenAI `dimensions` parameter outright:

```
Model 'cyberlink-embed' does not support Matryoshka embeddings;
dimensions must be unset (received dimensions=1024).
```

An OpenSearch `knn_vector` mapping fixes its dimension at creation, so a consumer that
indexed at 4096 does not degrade when the model changes — it stops working, and the
index has to be deleted and rebuilt rather than migrated. **Pick the embedding model
before building the index, and treat its dimension as part of the index schema**, not
as a serving parameter that can be tuned later.

## Setup

[vLLM 0.28.0, `--runner pooling`](vllm/) — one container beside the chat model, behind
the same router.
