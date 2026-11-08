# vLLM 0.33.0, Docker — DeepSeek-V4-Flash-0731 on four cards

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0`, unpatched |
| Checkpoint | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) — 167 GB, FP8 e4m3, 128×128 blocks |
| Cards | 4 of 4, TP=4 with expert parallelism |
| Kernels vLLM picks by itself | MoE `DEEPGEMM_MXFP4`, FP8 indexer cache, FlashInfer SM120 sparse-MLA decode, KV format `fp8_ds_mla` |
| KV pool | 1,557,249 tokens — 5.9 full-length requests |
| VRAM per card | 88,039 MiB; weights 37.8 GiB |
| Start to ready | **522 s** — weights 23 s, engine init 456 s (graph capture, FlashInfer autotune); 572 s with DSpark |

```
vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --enable-expert-parallel
  --gpu-memory-utilization 0.90 --max-model-len 262144 --trust-remote-code
  --kv-cache-dtype fp8 --block-size 256 --tokenizer-mode deepseek_v4
  --default-chat-template-kwargs '{"thinking":true}'
  --reasoning-parser deepseek_v4 --tool-call-parser deepseek_v4 --enable-auto-tool-choice
  [--speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}']
```

**The August blocker is gone.** vLLM 0.27 aborted on sm120 in DeepGEMM's hyper-connection
kernel ([why the SGLang patchset was needed](../sglang/README.md#why-it-runs-at-all)); 0.33
has its own fallbacks and runs the checkpoint with the image as published. This is the
recipe's `single_node_tep` on four cards instead of eight, and it serves the DSpark draft
module of the checkpoint too.

## Four copies need one changed line

**Four data-parallel copies with expert parallelism**, the recipe's `single_node_dep` and the
layout the August stack used for attention, fail in the stock image: the copies load (43 GiB
each), profile and then stop during graph capture, where FlashInfer's SM120 sparse-MLA decode
raises `attention workspace insufficient for resolved plan`. vLLM reserves a fixed 128 MiB for
that kernel; with one card per copy each card computes all 64 heads, at TP=4 it is 16.
Raising the constant to 1 GiB in a mounted copy of the file is enough, and then
[four copies](scenarios/data-parallel.md) deliver **11,535 tok/s at 1,024 clients**, twice
the TP=4 layout, at a fifth less single-stream speed. The same constant also stops the full
1,048,576-token window at TP=4; with 1 GiB it starts and finds every needle at
[960k](scenarios/long-context.md#full-context).

## Pinned values

| Request, "17 × 23" | completion tokens | reasoning tokens |
|---|---|---|
| nothing (server default `thinking: true`) | 16–17 | 13 |
| `chat_template_kwargs: {thinking: false}` | 2 | 0 |
| `reasoning_effort: "none"` | 2 | 0 |
| `chat_template_kwargs: {enable_thinking: false}` | 16 | 13 — no effect while the server sets `thinking` |

`thinking: false` is the off switch used in every scenario. vLLM counts the reasoning tokens
for this parser, so the protocol's check works as written. Tool calls come back as
`tool_calls` with the `deepseek_v4` parser.
