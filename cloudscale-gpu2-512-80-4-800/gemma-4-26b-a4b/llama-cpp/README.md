# llama.cpp, single card

**Gemma-4-26B-A4B-it in BF16 on one RTX PRO 6000, with MTP speculative decoding**

The fastest of the three models measured on this machine in this configuration, and the
one that makes the case for a sparse model on a single card: 2.6× the throughput of the
dense Gemma-4-31B at concurrency 32, with 3.9× better median latency.

**Machine:** [cloudscale.ch `GPU2-512-80-4-800`](../../README.md) ·
**Model:** [Gemma-4-26B-A4B](../README.md)

| | |
|---|---|
| Engine | llama.cpp, commit `10bf611e` (2026-08-16), built same day |
| Image | `llamacpp-sm120:20260816`, built from [the Dockerfile](../../deepseek-v4-flash-0731/llama-cpp/Dockerfile) |
| Build | CUDA 13.0.1 · gcc 13.3.0 · `CMAKE_CUDA_ARCHITECTURES=120` |
| Weights | `unsloth/gemma-4-26B-A4B-it-GGUF`, `BF16/` — 46.5 + 0.5 GB |
| Draft | `MTP/mtp-gemma-4-26B-A4B-it-BF16.gguf` — 0.8 GB |
| Architecture | `gemma4` + `gemma4-assistant` (the draft) |
| GPU | 1 card, `CUDA_VISIBLE_DEVICES` pinned |
| VRAM | 55,203 MiB of 97,887 |
| Startup | 15 s to healthy |

---

## Measured scenarios

| Scenario | Headline |
|---|---|
| [Single stream](scenarios/single-stream.md) | 189.8 output tok/s · p50 2.80 s |
| [Concurrent load](scenarios/concurrent-load.md) | **816.9 output tok/s** at C=32 · scaling had not flattened |
| [Reasoning cost](scenarios/reasoning-cost.md) | thinking off = **2.6× answers/s** and a 25× longer visible answer |

---

## Deployment

```bash
docker run -d --name g26 --restart unless-stopped \
  --gpus all -e CUDA_VISIBLE_DEVICES=1 \
  -p $BIND:8002:8080 \
  -v /mnt/scratch/models:/models:ro \
  llamacpp-sm120:20260816 \
  llama-server \
    -m  /models/gemma-4-26B-A4B-GGUF/BF16/gemma-4-26B-A4B-it-BF16-00001-of-00002.gguf \
    -md /models/gemma-4-26B-A4B-GGUF/MTP/mtp-gemma-4-26B-A4B-it-BF16.gguf \
    --spec-type draft-mtp --spec-draft-n-max 2 \
    -ngl 99 -ngld 99 -c 32768 -np 16 -fa on --jinja \
    --temp 1.0 --top-p 0.95 --top-k 64 \
    --host 0.0.0.0 --port 8080
```
`$BIND` is the address the server should listen on. Publishing to `0.0.0.0` exposes an
unauthenticated inference endpoint on every interface the host has — bind it to a private
or VPN address instead, and check what is actually reachable rather than assuming the
host firewall covers it.


Point `-m` at the **first** shard; llama.cpp finds the rest of the split itself. The
`mmproj-*.gguf` files in the same repository are for vision input and are not used here.

## Pinned values

Conditions, not recommendations.

| Setting | Value | Failure mode otherwise |
|---|---|---|
| `-c` × slots | 32,768 with `-np 16` | `-c 65536` needs 38.4 GB of KV and the process exits at load with `cudaMalloc failed`. `-c` ÷ `-np` is the per-slot budget and must exceed prompt + `max_tokens`; at `-np 32` each slot gets 1024 tokens, which truncates the protocol prompt |
| Thinking switch | `enable_thinking` | `thinking` — the protocol default and DeepSeek-V4's key — is accepted and silently ignored |
| `reasoning_effort` | not used | inert on this checkpoint: 509 against 508 tokens per answer |
| Sampling | `1.0 / 0.95 / 64` | the checkpoint's documented calibration; not varied here |

## MTP helps throughput, and does not explain the utilisation curve

Both Gemma runs lose GPU utilisation as concurrency rises, and speculative decoding was
the obvious suspect. A control run of this model with `--spec-type` removed and
everything else identical says otherwise:

| Concurrent | with MTP | without MTP | MTP gain | GPU with | GPU without |
|---|---|---|---|---|---|
| 1 | 190.1 | 127.4 | **+49 %** | 88 % | 89 % |
| 4 | 367.5 | 268.8 | +37 % | 74 % | 79 % |
| 8 | 499.9 | 407.9 | +23 % | 66 % | 71 % |
| 16 | 625.3 | 608.7 | +3 % | 59 % | 56 % |
| 32 | **816.9** | 612.5 | **+33 %** | 49 % | 58 % |

Output tokens per second. Utilisation falls either way — 89 % to 58 % without
speculation — so the draft-verify cycle is not what empties the card.

What is: llama.cpp's batching. The [engine comparison](../engine-comparison.md) runs this
same model on this same card under vLLM at **100 % utilisation on every level**, which
rules out both the speculation theory and the compute-per-token theory that replaced it.

Two things the control does establish:

**MTP pays at every level measured**, most at low concurrency where there is no batch to
hide behind, and still a third at 32.

**MTP extends the range that scales.** Without it, throughput plateaus between 16 and 32
(608.7 → 612.5). With it, the same step gains 31 % (625.3 → 816.9).

## Still open

- `--spec-draft-n-max` is at 2, the value the model card suggests. 1 and 3 were not tried
- Slot count. 16 was chosen so all three models on this machine share one configuration;
  this model had 42 GB of card left and would carry more
- Where exactly llama.cpp loses the time. The engine comparison establishes *that* the
  batching is the cause — same model, same card, 100 % under vLLM against 32 % here —
  but not which part of the scheduler, which would need a profile rather than a sweep
