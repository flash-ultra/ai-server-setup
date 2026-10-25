# Qwen3-Embedding-8B

An embedding model sharing both cards with
[Qwen3.8-27B](../qwen3-8-27b/) on
[cloudscale `GPU2-256-40-2-1600`](../README.md). Set up 2026-10-24, **replaced on
2026-10-25 by [Qwen3-Embedding-4B](../qwen3-embedding-4b/)** when the chat model
changed and left 6.5 GiB per card instead of 14.1. The dimension went 4096 → 2560
with it, which is an index rebuild rather than a setting.

| | |
|---|---|
| Checkpoint | [`Qwen/Qwen3-Embedding-8B`](https://huggingface.co/Qwen/Qwen3-Embedding-8B) |
| Size on disk | 14.1 GiB, BF16 |
| Output dimension | **4096** |
| Cards | 2 of 2 (TP=2), **alongside the chat model** |
| Served as | `cyberlink-embed` on `127.0.0.1:8002` |

## Verdict

**It is the capability, not a measurement.** This directory documents a configuration
that works; there is no `v1` series and no retrieval benchmark. The model is here
because OpenMetadata needs embeddings and the strongest one that fits was wanted — and
it fits in 14,104 MiB per card next to a 27 B chat model at full precision.

A functional check, not a benchmark: the same sentence in German and English embeds to
cosine similarity **0.850**, against **0.406** for an unrelated sentence. Three vectors,
4096 dimensions each, 0.03 s through the router.

## Setup

[vLLM 0.28.0, `--runner pooling`](vllm/) — one container, no separate inference stack.
