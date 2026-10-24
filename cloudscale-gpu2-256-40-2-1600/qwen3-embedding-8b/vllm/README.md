# vLLM 0.28.0 — Qwen3-Embedding-8B beside a chat model

Second container on the same two cards, stock upstream image.

## Configuration in effect

```
serve --model /model --served-model-name cyberlink-embed
  --host 127.0.0.1 --port 8002
  --runner pooling
  --tensor-parallel-size 2 --trust-remote-code
  --gpu-memory-utilization 0.14 --max-model-len 8192
```

| | |
|---|---|
| VRAM | 14,104 MiB per card |
| Combined with the chat model | 95,230 of 97,887 MiB per card |
| Restart policy | `unless-stopped` — comes back after a reboot |

## Pinned values

| Setting | Value | What happens if you deviate |
|---|---|---|
| `--runner pooling` | required | **`--task embed` no longer exists in 0.28** and the engine exits on an unrecognised argument. Most guides still show the old flag |
| `--gpu-memory-utilization` | **0.14** | the fraction is of the **whole card, not of what is free**. `0.95` beside a model already holding 82 % does not mean "95 % of the remainder" — it means 90 GiB, and the engine aborts out of memory while 14.78 GiB sit unused. Size this as `wanted_GiB / 95.6` |
| `--max-model-len` | 8192 | the input limit per embedding request. Larger costs KV for a workload that does not generate |

**The utilisation flag is the one that bites.** It reads like a share of free memory and
is a share of the card. Every co-tenancy decision on this machine has to be computed
against 97,887 MiB total, not against what `nvidia-smi` reports as free.

## Routing

Both services sit behind one port, because the gateway expects a single upstream.
`api-router.py` dispatches on the request path — anything containing `/embeddings` goes
to 8002, everything else to 8001 — and runs as a systemd unit with `Restart=always`, so
the split survives a reboot like the two containers do.
