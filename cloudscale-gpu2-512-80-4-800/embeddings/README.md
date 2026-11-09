# Embeddings on four cards

Four embedding models on [this machine](../README.md), measured 2026-11-08 under protocol
[`e1`](../../benchmark/README.md#embeddings-protocol-e1): throughput, query latency and
retrieval quality on one English and three German tasks. Every model runs as **four copies,
one per card**, under vLLM 0.33.0 with `--runner pooling`.

| Model | Parameters, dimensions | Context | Checkpoint |
|---|---|---|---|
| BAAI bge-m3 | 0.57 B, 1,024 | 8,192 | [`BAAI/bge-m3`](https://huggingface.co/BAAI/bge-m3), MIT — the common multilingual baseline |
| Qwen3-Embedding-8B | 8 B, 4,096 | 32,768 | [`Qwen/Qwen3-Embedding-8B`](https://huggingface.co/Qwen/Qwen3-Embedding-8B), Apache 2.0 |
| harrier-oss-v1-27b | 27 B, 5,376 | 32,768 | [`microsoft/harrier-oss-v1-27b`](https://huggingface.co/microsoft/harrier-oss-v1-27b), MIT — Gemma 3 base, 74.3 on Multilingual MTEB v2 according to its card |
| Nemotron-3.5-Embed-8B | 8 B, 4,096 | 32,768 | [`nvidia/Nemotron-3.5-Embed-8B-BF16`](https://huggingface.co/nvidia/Nemotron-3.5-Embed-8B-BF16), OpenMDW-1.1 — Ministral 3 base, text and images, released 2026-10-07 |

## Verdict

**Nemotron-3.5-Embed-8B wins every quality task, at the speed of an 8 B model.** It leads
on English science claims, on both German QA sets and, by the widest margin, on German court
decisions, where it is 8 points of nDCG@10 ahead of the next model. The 27 B harrier, three
times the compute per token, comes second on three tasks and last on GermanDPR.

**bge-m3 is about 18 times faster than the 8 B models** and the only one that embeds a corpus of
ten thousand court decisions in under a minute. On short German QA it holds its own; on
the court decisions it falls 23 points behind Nemotron.

**Four copies are exactly four times one card**, for every model. One card is saturated
from two clients on; more clients only lengthen requests.

**FP8 on the fly is free speed.** `--quantization fp8` gives Qwen and harrier 1.7 times the
throughput, and no task moves by more than 0.004 nDCG@10.

| Four cards, BF16 | bge-m3 | Qwen3-Embedding-8B | harrier-oss-v1-27b | Nemotron-3.5-Embed-8B |
|---|---|---|---|---|
| **SciFact** nDCG@10 (English) | 0.644 | 0.784 | 0.800 | **0.833** |
| **GermanQuAD** nDCG@10 | 0.956 | 0.970 | 0.977 | **0.987** |
| **GermanDPR** nDCG@10 | 0.825 | 0.844 | 0.809 | **0.870** |
| **GerDaLIR** nDCG@10 (court decisions) | 0.320 | 0.450 | 0.471 | **0.547** |
| Ingest, 512-token chunks | **1,160,029 tok/s** · 2,318 chunks/s | 65,273 · 130 | 18,184 · 36 | 61,845 · 124 |
| One card | **291,754 tok/s** | 16,709 | 4,677 | 15,767 |
| GerDaLIR corpus, 9,969 decisions cut at 8,192 tokens | **53 s** for 39.3 M tokens | 13.0 min for 45.4 M | 36.7 min for 39.6 M | 15.7 min for 46.1 M |
| One query, one at a time, p50 | **6.0 ms** | 14.9 ms | 43.9 ms | 15.6 ms |
| Queries/s, four copies | **≥ 4,989** | ≥ 3,610 | ≥ 828 | ≥ 2,386 |
| One ~31k-token document | — (8k: 64 ms) | 3.2 s | 7.1 s | 4.0 s |
| GPU memory per card | **2.1 GiB** | 85.6 GiB | 85.2 GiB | 17.2 GiB |

Quality with the MTEB query prompt; how much the prompt moves it is [below](#the-query-prompt-moves-results-by-up-to-ten-points).
Memory is what vLLM holds at `--gpu-memory-utilization 0.90`: for the causal models Qwen and harrier
it pre-allocates a KV cache, for bge-m3 and Nemotron it allocates none, so those two would
fit beside a language model on the same card.

## Ingest

Clients send 32 chunks of about 512 tokens per request, cut at random offsets from a mixed
English and German text pool. Throughput is input tokens over the real run time.

| Clients (four copies) | bge-m3 | Qwen3-Embedding-8B | harrier-oss-v1-27b | Nemotron-3.5-Embed-8B |
|---:|---:|---:|---:|---:|
| 4 | 653,710 tok/s | 62,828 | 17,508 | 57,221 |
| 8 | 1,124,568 | 64,385 | 17,436 | 58,054 |
| 16 | **1,160,029** | **65,273** | **18,184** | 60,890 |
| 32 | 1,154,187 | 65,009 | 18,154 | **61,845** |
| 64 | 1,142,647 | 65,269 | 18,146 | 61,474 |
| 128 | 1,128,737 | 64,692 | 18,102 | 61,314 |
| p50 request at 128 | 1.8 s | 30.4 s | 72.8 s | 31.1 s |

Per hour on four cards that is 8.3 M chunks for bge-m3, 470 k for Qwen, 445 k for Nemotron and
130 k for harrier. During the harrier corpus run all four cards sat at their 300 W limit and
92–100 % utilisation.

## Queries

Real queries from SciFact and GermanQuAD in each model's query format, one query per request.

| | bge-m3 | Qwen3-Embedding-8B | harrier-oss-v1-27b | Nemotron-3.5-Embed-8B |
|---|---:|---:|---:|---:|
| One at a time, p50 / p99 | 6.0 / 8.3 ms | 14.9 / 17.5 ms | 43.9 / 45.5 ms | 15.6 / 18.6 ms |
| 16 clients, one client process | 1,481 q/s, p50 10 ms | 641 q/s, 25 ms | 195 q/s, 81 ms | 556 q/s, 27 ms |
| 64 clients, one client process | 1,903 q/s, 33 ms | 1,142 q/s, 55 ms | 583 q/s, 108 ms | 639 q/s, 100 ms |
| 256 clients, one client process | 1,842 q/s, 129 ms | 1,086 q/s, 224 ms | 828 q/s, 291 ms | 589 q/s, 407 ms |
| 64 clients in each of several processes | **4,989 q/s** (3 processes), p50 38 ms | **3,610 q/s** (4), 69 ms | not run | **2,386 q/s** (4), 105 ms |

**One Python client process is the limit, not the servers.** Its rate stays almost the same
as processes are added — Qwen 1,113, then 1,127, 1,018 and 902 q/s per process, Nemotron
640 to 597 — so the total grows nearly in step, and it was still rising at the last step.
The bottom row is therefore a lower bound for the four servers. harrier's 828 q/s, at 28
tokens per query about 23,000 tok/s, already exceed its ingest rate; it was not repeated
with more processes.

## Long documents

One document per request on one card, median of three:

| Tokens | bge-m3 | Qwen3-Embedding-8B | harrier-oss-v1-27b | Nemotron-3.5-Embed-8B |
|---:|---:|---:|---:|---:|
| ~2,000 | 16 ms | 122 ms | 427 ms | 131 ms |
| ~8,000 | 64 ms | 564 ms | 1.78 s | 669 ms |
| ~31,000 | — | 3.19 s | 7.08 s | 4.01 s |

The 8 B models slow down at 32k (9.7 and 7.7 k tok/s against 15.6 and 14.6 k at 2k). harrier stays
flat at 4.3–4.5 k; five in six of its layers attend over a 1,024-token sliding window.

## FP8 on the fly

The same servers with `--quantization fp8`, which quantises the weights at load time. Nothing
else changes.

| | Qwen3-Embedding-8B BF16 | FP8 | harrier-oss-v1-27b BF16 | FP8 |
|---|---:|---:|---:|---:|
| Ingest, four cards | 65,273 tok/s | **113,365** (1.74×) | 18,184 | **30,470** (1.68×) |
| One card | 16,709 | 29,144 | 4,677 | 7,837 |
| GerDaLIR corpus | 13.0 min | **8.1 min** | 36.7 min | **22.2 min** |
| One query, p50 | 14.9 ms | 10.3 ms | 43.9 ms | 24.9 ms |
| One ~31k-token document | 3.19 s | 2.40 s | 7.08 s | 4.42 s |
| Weights per card | 14.1 GiB | 7.9 GiB | 50.7 GiB | 27.0 GiB |
| SciFact nDCG@10 | 0.784 | 0.780 | 0.800 | 0.797 |
| GermanQuAD | 0.970 | 0.971 | 0.977 | 0.978 |
| GermanDPR | 0.844 | 0.843 | 0.809 | 0.810 |
| GerDaLIR | 0.450 | 0.449 | 0.471 | 0.469 |

The largest change in quality is 0.004 nDCG@10 on SciFact for Qwen. Nemotron and bge-m3 were
not run in FP8.

## The query prompt moves results by up to ten points

Qwen and harrier expect a one-sentence task instruction in front of every query. MTEB has
none for the three German tasks and uses its retrieval default, "Retrieve text based on
user query."; with that prompt the Qwen numbers reproduce the published ones. A more
specific instruction, "Given a question, retrieve passages that answer the question", does
not help both models the same way:

| nDCG@10 | GermanQuAD | GermanDPR | GerDaLIR¹ |
|---|---|---|---|
| Qwen3-Embedding-8B, MTEB default / specific | **0.970** / 0.926 | **0.844** / 0.749 | 0.450 / **0.464** |
| harrier-oss-v1-27b, MTEB default / specific | 0.977 / **0.978** | 0.809 / **0.848** | 0.471 / — |

¹ Specific instruction for GerDaLIR: "Given a passage from a German court decision, retrieve
the court decisions it refers to".

The same sentence costs Qwen 9.5 points on GermanDPR and gains harrier 3.9. Test the prompt
on your own data before trusting a leaderboard ranking. bge-m3 takes no instruction;
Nemotron has fixed `query:` and `passage:` prefixes.

## Raw results

Each model directory holds the outputs as written by the scripts:
[bge-m3](results/bge-m3/), [Qwen3-Embedding-8B](results/qwen3-embedding-8b/),
[harrier-oss-v1-27b](results/harrier-oss-v1-27b/), [Nemotron-3.5-Embed-8B](results/nemotron-3-5-embed-8b/),
and the FP8 runs [Qwen3-Embedding-8B FP8](results/qwen3-embedding-8b-fp8/) and
[harrier-oss-v1-27b FP8](results/harrier-oss-v1-27b-fp8/). `quality.md` uses the MTEB prompt
except for Qwen, whose first run used the specific instruction; its MTEB-prompt run is
`quality-mteb-prompt.md`. `query-<n>-procs.md` holds the runs with several client processes.

## Setup

```bash
docker run -d --gpus device=0 --ipc=host --network host \
  -v /opt/llm/hf:/opt/llm/hf -e HF_HOME=/opt/llm/hf -e HF_HUB_OFFLINE=1 \
  vllm/vllm-openai:v0.33.0 Qwen/Qwen3-Embedding-8B --served-model-name cyberlink \
  --host 127.0.0.1 --port 8001 --runner pooling --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

The same for `device=1..3` on ports 8002–8004. No other flags: all four models load without
patches on sm120, and bge-m3 and Qwen reproduce their published MTEB scores with vLLM's
defaults. bge-m3 takes `--max-model-len 8192`. Nemotron additionally takes
`--chat-template-content-format openai` and is called on `/v2/embed` with
`input_type: query` or `document`, as its model card shows.
