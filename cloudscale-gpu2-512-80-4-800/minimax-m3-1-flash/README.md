# MiniMax-M3.1-Flash — does not run on sm120 yet

Tried on all four cards of [this machine](../README.md) on 2026-11-06, one day after the
release. Three engine configurations, three different walls; nothing was measured.

| | |
|---|---|
| Checkpoint | [`MiniMaxAI/MiniMax-M3.1-Flash`](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) — 252.4 GB |
| Architecture | `MiniMaxM3SparseForConditionalGeneration`, 60 layers, 128 experts (4 routed), MiniMax Sparse Attention (MSA) on every layer, 1 M context, text + image + video |
| Quantisation, as shipped | **mixed**: `quant_method: mxfp8` for attention and dense weights (block 32), but `moe_quant_algo: NVFP4`, `moe_quant_format: nvfp4-pack-quantized` for the routed experts — `weight_packed` U8 at half the input width, E4M3 block scales every 16 values, an F32 global scale per expert |

## What happened

| Engine | Result | Why |
|---|---|---|
| vLLM 0.33.0, stock image | **CUDA out of memory before the weights load** — 93.6 GiB allocated per card | vLLM reads `quant_method: mxfp8` and ignores `moe_quant_algo`; it allocates the experts as 8-bit, twice their real size. The `moe_quant_algo` key is only handled for DeepSeek-V4/V4.1 in this release |
| SGLang 0.5.23, stock image | **refused at startup**: `TRTLLM FMHAv2 prefill on SM120 does not support fp8_e4m3 KV cache` | SGLang recognises the mixed checkpoint ("serving as minimax_m3_nvfp4") and then requires an FP8 KV cache and the `trtllm_mha` backend, which has no FP8-KV prefill on sm120. With `--attention-backend triton` it gets further and stops on the missing MSA kernels (`No module named 'inference'`) |
| SGLang `dev-minimax-m31-flash` image (2026-10-23), MSA kernels 0.1.0 included | **weights loaded** (61.4 GB per card in 14 s, experts correctly at 4 bit), then `ValueError: decode indexer plan requires SM100 or SM103` | MiniMax's sparse-attention kernels are built for the datacenter Blackwell parts only. sm120 (RTX PRO 6000, RTX 50) has no decode indexer |

**The blocker is the attention, not the quantisation.** The NVFP4 experts load fine once an
engine reads the checkpoint correctly; the MSA indexer that every layer of this model runs
exists only for SM100/SM103. Until MiniMax's MSA kernels gain an sm120 path, or an engine
ships a generic fallback, the model does not serve on this hardware.

**A GGUF route exists but is not upstream.** unsloth publishes GGUFs (UD-Q4_K_XL 249 GB),
and llama.cpp has a `minimax-m3` architecture, but M3.1 needs pull request
[#31192](https://github.com/ggml-org/llama.cpp/pull/31192) ("model: add MiniMax-M3.1"), open
and unmerged as of this date. Not tried here.
