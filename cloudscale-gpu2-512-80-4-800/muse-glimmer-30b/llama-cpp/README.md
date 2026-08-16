# llama.cpp, single card

**Muse-Glimmer-30B in BF16 on one RTX PRO 6000, without speculative decoding**

**Machine:** [cloudscale.ch `GPU2-512-80-4-800`](../../README.md) ·
**Model:** [Muse-Glimmer-30B](../README.md)

| | |
|---|---|
| Engine | llama.cpp, commit `10bf611e` (2026-08-16), built same day |
| Image | `llamacpp-sm120:20260816` · CUDA 13.0.1 · gcc 13.3.0 · arch 120 |
| Weights | `unsloth/Muse-Glimmer-30B-GGUF`, `BF16/` — 27.8 + 24.1 GB |
| Draft | none — no MTP file in this GGUF package |
| Architecture | `muse-glimmer` — present in llama.cpp master, in neither SGLang nor vLLM here |
| VRAM | 53,019 MiB of 97,887 |
| Startup | 15 s to healthy |

## Measured scenarios

| Scenario | Headline |
|---|---|
| [Single stream](scenarios/single-stream.md) | 30.9 output tok/s · p50 14.78 s · 97 % GPU |
| [Concurrent load](scenarios/concurrent-load.md) | 520.5 tok/s at C=32 · **92–99 % utilisation throughout** |
| [Reasoning cost](scenarios/reasoning-cost.md) | `reasoning_effort=low` = 1.8× answers/s; template switch inert |

## Deployment

```bash
docker run -d --name muse --restart unless-stopped \
  --gpus all -e CUDA_VISIBLE_DEVICES=2 \
  -p 100.102.25.81:8003:8080 \
  -v /mnt/scratch/models:/models:ro \
  llamacpp-sm120:20260816 \
  llama-server \
    -m /models/Muse-Glimmer-30B-GGUF/BF16/Muse-Glimmer-30B-BF16-00001-of-00002.gguf \
    -ngl 99 -c 32768 -np 16 -fa on --jinja \
    --temp 1.0 --top-p 0.95 --top-k 64 \
    --host 0.0.0.0 --port 8080
```

## Pinned values

| Setting | Value | Failure mode otherwise |
|---|---|---|
| Reasoning control | `reasoning_effort` | the chat template has no thinking switch; `thinking` and `enable_thinking` are both accepted and do nothing |
| `-c` / `-np` | 32,768 / 16 | kept identical to the other two models on this machine so the comparison holds one configuration; this model has 44 GB of card left and would carry more |
| Engine | llama.cpp only | `muse-glimmer` is unknown to the SGLang and vLLM images on this machine |

## Still open

- Speculative decoding — `meta-models/Muse-Glimmer-30B-assistant` exists but was never
  converted to GGUF or tried
- A newer SGLang or vLLM that knows the architecture, which would make this model part of
  the [engine comparison](../../gemma-4-26b-a4b/engine-comparison.md)
