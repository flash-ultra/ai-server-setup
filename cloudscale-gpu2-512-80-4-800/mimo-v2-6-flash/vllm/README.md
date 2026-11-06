# vLLM 0.33.0, Docker — MiMo-V2.6-Flash-RL on four cards

Stock `vllm/vllm-openai:v0.33.0`, not the vendor `mimo-v26` image the two-card series needed:
vLLM 0.33 knows the architecture and builds the sm120 kernels on its own. Measured 2026-11-06.

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` (torch 2.14.0+cu130) |
| Checkpoint | [`XiaomiMiMo/MiMo-V2.6-Flash-RL`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) — 177.7 GB, FP8 |
| Resolved architecture | `MiMoV2OmniForCausalLM` (the config declares `MiMoV2ForCausalLM`; see the [two-card page](../../../cloudscale-gpu2-256-40-2-1600/mimo-v2-6-flash/vllm/README.md#the-checkpoint-declares-a-text-architecture-and-gets-loaded-as-a-multimodal-one)) |
| Cards | 4 of 4 (TP=4) |
| Context served | 262,144 |
| KV pool | **4,294,730 tokens** — 16.38 full-length requests |
| VRAM per card | 85,979 MiB of 97,887 |
| Start to ready | ≈ 250 s — weights 34.5 s, engine init 144.9 s (compilation 27.1 s) |

## Configuration in effect

```
vllm serve XiaomiMiMo/MiMo-V2.6-Flash-RL --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --trust-remote-code
  --gpu-memory-utilization 0.90 --max-model-len 262144
  --reasoning-parser mimo --tool-call-parser mimo --enable-auto-tool-choice
  --override-generation-config '{"max_new_tokens": 32768}'
VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0
```

The last two lines come from the two-card series: without the override the checkpoint's
`generation_config.json` caps every reply at 2,048 tokens, and the profiler estimate cost
that machine three quarters of its window. Neither was re-tested here; on four cards the
window is not tight at `0.90`.

## Pinned values

| Setting | Value | Verified 2026-11-06 |
|---|---|---|
| `--reasoning-parser` | `mimo` | thinking text in `message.reasoning`, `reasoning_tokens` reported |
| `--tool-call-parser` | `mimo` | weather question with one tool → `finish_reason: tool_calls`, `get_weather({"city": "Zurich"})` |
| thinking switch | `enable_thinking: false` **or** `reasoning_effort: "none"` | `reasoning_tokens` 11 → 0 under both |
