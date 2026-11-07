# vLLM 0.33.0, Docker — Nemotron-3-Super NVFP4, four copies

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` |
| Checkpoint | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4) — 80 GB |
| Parallelism | `--data-parallel-size 4`, TP=1: one full copy per card, one API endpoint |
| KV pool | 10,680,687 tokens per copy, FP8 |
| VRAM per card | 85,867 MiB |
| Start to ready | **321 s** — engine init 208 s (compilation 27 s) |

## Configuration in effect

```
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 1 --data-parallel-size 4
  --gpu-memory-utilization 0.90 --max-model-len 262144 --trust-remote-code
  --kv-cache-dtype fp8 --mamba-ssm-cache-dtype float16 --async-scheduling
  --reasoning-parser nemotron_v3 --tool-call-parser qwen3_coder --enable-auto-tool-choice
```

NVIDIA's card loads its reasoning parser as a plugin file from the repository
(`--reasoning-parser-plugin super_v3_reasoning_parser.py --reasoning-parser super_v3`);
vLLM 0.33 ships the same parser as `nemotron_v3`, so no repository code runs.

## Pinned values

| Request | `reasoning_tokens` on "17×23" |
|---|---|
| default | 64 |
| `chat_template_kwargs: {enable_thinking: false}` | **0** |
| `reasoning_effort: "none"` | 0 |
| `reasoning_effort: "low"` | 47 — the model's own low setting is `chat_template_kwargs: {low_effort: true}` |

**All four cards run at 100 % even with one client.** Data parallelism over a
mixture-of-experts model keeps idle copies stepping in lockstep with dummy batches; the
utilisation column below says nothing about how busy a copy really is.
