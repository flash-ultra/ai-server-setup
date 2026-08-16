# llama.cpp, single card

**Gemma-4-31B-it in BF16 on one RTX PRO 6000, with MTP speculative decoding**

**Machine:** [cloudscale.ch `GPU2-512-80-4-800`](../../README.md) ·
**Model:** [Gemma-4-31B](../README.md)

| | |
|---|---|
| Engine | llama.cpp, commit `10bf611e` (2026-08-16), built same day |
| Image | `llamacpp-sm120:20260816` · CUDA 13.0.1 · gcc 13.3.0 · arch 120 |
| Weights | `unsloth/gemma-4-31B-it-GGUF`, `BF16/` — 46.5 + 10.7 GB |
| Draft | `MTP/mtp-gemma-4-31B-it-BF16.gguf` — 0.9 GB |
| VRAM | **82,129 MiB** of 97,887 — 15 GB spare |
| Startup | 15 s to healthy |

## Measured scenarios

| Scenario | Headline |
|---|---|
| [Single stream](scenarios/single-stream.md) | 54.8 output tok/s · p50 8.10 s |
| [Concurrent load](scenarios/concurrent-load.md) | stalls between 8 and 16 · 310.2 tok/s at C=32 |
| [Reasoning cost](scenarios/reasoning-cost.md) | thinking off saves 12× tokens and **no** time |

## Deployment

```bash
docker run -d --name g31 --restart unless-stopped \
  --gpus all -e CUDA_VISIBLE_DEVICES=0 \
  -p $BIND:8001:8080 \
  -v /mnt/scratch/models:/models:ro \
  llamacpp-sm120:20260816 \
  llama-server \
    -m  /models/gemma-4-31B-GGUF/BF16/gemma-4-31B-it-BF16-00001-of-00002.gguf \
    -md /models/gemma-4-31B-GGUF/MTP/mtp-gemma-4-31B-it-BF16.gguf \
    --spec-type draft-mtp --spec-draft-n-max 2 \
    -ngl 99 -ngld 99 -c 32768 -np 16 -fa on --jinja \
    --temp 1.0 --top-p 0.95 --top-k 64 \
    --host 0.0.0.0 --port 8080
```
`$BIND` is the address the server should listen on. Publishing to `0.0.0.0` exposes an
unauthenticated inference endpoint on every interface the host has — bind it to a private
or VPN address instead, and check what is actually reachable rather than assuming the
host firewall covers it.


## Pinned values

| Setting | Value | Failure mode otherwise |
|---|---|---|
| `-c` | **32,768** | `65536` needs 38.4 GB of KV on top of 57 GB of weights; the process exits at load with `cudaMalloc failed: out of memory` |
| `-np` | 16 | `-c` ÷ `-np` is the per-slot budget and must exceed prompt + `max_tokens`; at 32 slots each gets 1024 tokens and the protocol prompt no longer fits |
| Thinking switch | `enable_thinking` | the protocol default `thinking` is accepted and ignored |
| Sampling | `1.0 / 0.95 / 64` | checkpoint calibration; not varied |

## Still open

- Whether more slots move the stall between 8 and 16 concurrent. With 15 GB of card left
  the room for a larger `-c` is limited, which is the constraint that set `-np 16`
- `--spec-draft-n-max` other than 2
