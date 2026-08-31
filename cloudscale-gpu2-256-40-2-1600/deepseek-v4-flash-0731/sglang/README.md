# SGLang + SM120 patchset — 0731 on two cards

The image built for the [four-card machine](../../../cloudscale-gpu2-512-80-4-800/deepseek-v4-flash-0731/sglang/),
run here at TP=2. Tested 2026-08-30.

| | |
|---|---|
| Image | `ghcr.io/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000:latest`, 46 GB |
| Checkpoint | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) — 155.4 GiB |
| Cards | 2 of 2 (TP=2) |
| Context served | 262,144 |
| KV pool | `max_total_num_tokens` 1,382,912 · `max_running_requests` 256 |
| Memory in use | 95,649 MiB per card of 97,887 |
| Time to `/health` 200 | ~5 minutes |

**The image name says four cards; the card count is a launch flag, not a build decision.**
`--tp-size 2` starts without complaint. The image ships no entrypoint script of its own
(entrypoint is NVIDIA's wrapper, `CMD` is `/bin/bash`), so the server is invoked directly.

## Configuration in effect

```
python3 -m sglang.launch_server --model-path /model --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tp-size 2 --mem-fraction-static 0.93 --context-length 262144
  --trust-remote-code --kv-cache-dtype fp8_e4m3
  --reasoning-parser deepseek-v4 --tool-call-parser deepseekv4
```

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| `--kv-cache-dtype` | `fp8_e4m3` | `bf16` aborts at load with `AssertionError: bf16 is not supported for DeepseekV4ForCausalLM`, and a restart policy turns that into a loop |
| `--reasoning-parser` | `deepseek-v4` | without it the raw `<think>` block, closing tag included, lands in the middle of `content` |
| `--tool-call-parser` | `deepseekv4` | without it every request carrying `tool_choice` is rejected before the model sees it |
| `--mem-fraction-static` | `0.93` | 77.7 GiB of weights per card; the same value the NVFP4 release needs on this hardware |

## Scenarios

| Scenario | Status |
|---|---|
| [single stream](scenarios/single-stream.md) | measured |
| [concurrent load](scenarios/concurrent-load.md) | measured, two runs |
| [reasoning cost](scenarios/reasoning-cost.md) | measured — and it is the one that reframes the rest |
| [long context](scenarios/long-context.md) | measured |

## Still open

- **FP8 KV without scaling factors.** The only admissible setting, and the engine says it
  costs accuracy. Whether a checkpoint with KV scales exists was not investigated.
- **`--mem-fraction-static` not swept.** 0.93 was carried over from the NVFP4 setup.
- **1M context untried.** The pool would hold one such request.
