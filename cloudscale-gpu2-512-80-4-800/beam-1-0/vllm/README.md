# vLLM 0.33.0, Docker — Beam-1.0 NVFP4 on four cards

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` |
| Checkpoint | [`reflection/Beam-1.0-501B-A23B-NVFP4`](https://huggingface.co/reflection/Beam-1.0-501B-A23B-NVFP4) — 294 GB |
| Cards | 4 of 4, TP=4 |
| KV pool | 2,123,633 tokens, FP8 — 8.1 full-length requests |
| VRAM per card | 89,117 MiB |
| Start to ready | **150 s** — weights 25 s, engine init 60 s |

```
vllm serve reflection/Beam-1.0-501B-A23B-NVFP4 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --gpu-memory-utilization 0.90 --max-model-len 262144 --trust-remote-code
  --kv-cache-dtype fp8
  --reasoning-parser beam --tool-call-parser beam --enable-auto-tool-choice
```

Both parsers ship with vLLM 0.33. The card names no engine; NVFP4 runs on sm120 without
anything extra, as it did for GLM-5.3-Flash.

## Pinned values

| Request | `reasoning_tokens` on "17×23" |
|---|---|
| default (effort max, budget 512) | 73 |
| `chat_template_kwargs: {enable_thinking: false}` | 48 — not a switch of this template |
| `reasoning_effort: "none"` | rejected: the template raises on anything but an integer or minimal / low / medium / high / xhigh / max |
| `reasoning_effort: "low"` (budget 32) | 52 |

There is no thinking-off arm; `q1` measures `minimal` (budget 8, the smallest the model was
trained on) against the default.
