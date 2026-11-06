# vLLM 0.33.0, Docker — GLM-5.3-Flash NVFP4 on four cards

Stock `vllm/vllm-openai:v0.33.0`. The model card's own image (`glm53-flash-arm64-cu130`) is
built for arm64 and was not needed. Measured 2026-11-06.

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` (torch 2.14.0+cu130, transformers 5.20.2) |
| Checkpoint | [`nvidia/GLM-5.3-Flash-NVFP4`](https://huggingface.co/nvidia/GLM-5.3-Flash-NVFP4) — 204.4 GB, ModelOpt NVFP4 |
| Resolved architecture | `Glm5NextForConditionalGeneration` |
| Cards | 4 of 4, TP=4 with expert parallelism |
| FP4 kernels | FlashInfer `CutlassFp4GemmRunner`, autotuner config found for sm120 |
| Context served | 262,144 |
| KV pool | **4,291,550 tokens** in FP8 — 16.37 full-length requests |
| VRAM per card | 92,135–92,987 MiB of 97,887 |
| Start to ready | **431 s** — engine init 332.9 s |

## Configuration in effect

```
vllm serve nvidia/GLM-5.3-Flash-NVFP4 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --enable-expert-parallel --kv-cache-dtype fp8
  --gpu-memory-utilization 0.90 --max-model-len 262144 --trust-remote-code
  --reasoning-parser glm47 --tool-call-parser glm47 --enable-auto-tool-choice
```

Expert parallelism and the FP8 KV cache follow NVIDIA's card; the `glm47` parsers follow
vLLM's recipe for the FP8 original (the card names `glm45` for reasoning and no tool
parser).

## Pinned values

Verified 2026-11-06 against `usage.completion_tokens_details.reasoning_tokens`, same
question each time:

| Request | `reasoning_tokens` |
|---|---|
| no switch (default, effort max) | 7 |
| `chat_template_kwargs: {enable_thinking: false}` | **31** — ignored |
| `reasoning_effort: "none"` | **24** — ignored |
| `reasoning_effort: "low"` | 7 on this question; on the `v1` prompt **52 tokens, 2–4 % thinking** against 359 at default — see [reasoning cost](scenarios/reasoning-cost.md) |
| tool call, weather question | `finish_reason: tool_calls`, `get_weather({"city": "Zurich"})` |

**There is no thinking-off arm.** Both common keys are accepted and silently ignored, which
is exactly the false negative the protocol warns about. Every `v1` table below is the
default arm; `q1` measures `low` and the default.
