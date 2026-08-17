# DeepSeek-V4-Flash-NVFP4

NVIDIA's quantisation of DeepSeek-V4-Flash, served on **two** of the four cards of
[cloudscale `GPU2-512-80-4-800`](../README.md) — 4× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-08-17.

| | |
|---|---|
| Checkpoint | [`nvidia/DeepSeek-V4-Flash-NVFP4`](https://huggingface.co/nvidia/DeepSeek-V4-Flash-NVFP4) |
| Base model | [`deepseek-ai/DeepSeek-V4-Flash`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) — **a different release from [0731](../deepseek-v4-flash-0731/)** |
| Size on disk | 157 GB, 59 files |
| Architecture | `DeepseekV4ForCausalLM`, 43 layers, 256 experts (non-REAP), 6 active |
| Attention | MLA — Compressed Sparse + Heavily Compressed Attention |
| Quantisation | `fp8` / `MIXED_PRECISION`, `scale_fmt: ue8m0` |
| Native context | 1,048,576 · **262,144 served here** |
| Speculation | MTP, `num_nextn_predict_layers: 1`, module bundled in the checkpoint |

## Verdict

**One setup, and it delivers what its kit claims.**
[vLLM B12X at TP=2](vllm-b12x/) reproduces every published single-stream figure on this
machine, slightly better in each:

| | Kit / reference run | Measured here |
|---|---|---|
| TTFT | 197.8 ms | **173–193 ms** |
| Decode | 155.6 tok/s | **159.3–163.0 tok/s** |
| Draft acceptance | 58.0 % | **64.6 %** |
| Mean acceptance length | 2.16 | **2.29** |

Under load it reaches **9.97 answers/s at concurrency 256** (403.6 output tok/s, 12,513
total) on two cards. Two findings qualify that number, and both are in
[concurrent load](vllm-b12x/scenarios/concurrent-load.md): the curve is **not monotone** —
it dips at exactly `--max-num-seqs 64` — and the run-to-run spread in the middle of the
ladder reaches **74 %**, so the ladder describes a range, not an operating point. Neither
card ever passes 87 %.

**This is a test result, not a production recommendation.** Nothing was deployed on it;
production on this machine is [SGLang on the 0731 release](../deepseek-v4-flash-0731/).

## What this is not comparable to

The directory next door is **the same model family on a different release**, and the two
are not two setups of one model:

| | [`deepseek-v4-flash-0731/`](../deepseek-v4-flash-0731/) | here |
|---|---|---|
| Release | `DeepSeek-V4-Flash-0731` | `DeepSeek-V4-Flash` |
| Speculation | DSpark — **no MTP heads usable** | **MTP**, 2 draft tokens, 64.6 % acceptance |
| Quantisation | fp8 (BF16 checkpoint, GGUF Q8 for llama.cpp) | fp8 / `MIXED_PRECISION` NVFP4 |
| Cards | 4 (TP/DP/EP) | 2 (TP) |
| Engine | SGLang · llama.cpp | vLLM B12X |

The configs are architecturally identical — 43 layers, 256 experts, top-6,
`num_nextn_predict_layers: 1` in both — so a config diff alone does **not** distinguish
them, and MTP working here is not evidence that the 0731 entry's "DSpark only" is wrong.
Treat every number in the two directories as belonging to separate models.

One cross-setup comparison is worth stating, with that caveat attached: SGLang peaks at
[11.30 req/s on four cards](../deepseek-v4-flash-0731/sglang/scenarios/concurrent-load.md#configuration-sweep-protocol-v1)
against 9.97 here on two — **1.76× the requests per card**. Different release, different
quantisation, different engine, so this says the NVFP4 checkpoint gets useful throughput
out of half the machine; it does not rank the engines.

## Server setups

| Setup | Role | Engine | Startup |
|---|---|---|---|
| [`vllm-b12x/`](vllm-b12x/) | measured, not deployed | vLLM B12X SM120 build, TP=2 | 18 min cold · **18 min warm** |

### Scenario coverage

| Scenario | vLLM B12X |
|---|---|
| Single stream | [measured](vllm-b12x/scenarios/single-stream.md) |
| Concurrent load | [C 1–256, ladder twice + prompt mix](vllm-b12x/scenarios/concurrent-load.md) |
| Reasoning cost | [measured](vllm-b12x/scenarios/reasoning-cost.md) |
| Long context | not measured — nothing longer than ~1200 tokens was ever sent |

## Model-specific gotchas

**One flag decides both KV capacity and whether the server survives load.**
`--max-num-batched-tokens` at 512 gives a 56 % larger KV pool and then kills the engine at
concurrency 16 with a locked-workspace error; at 2048 the pool is smaller and the full
ladder to 256 completes twice.
[Both measurements, and the reason the two are linked](vllm-b12x/README.md#pinned-values).

**The KV pool is not limited by the weights.** 157 GB of weights on two 96 GB cards leaves
7.5–7.8 GiB for KV either way — what changes the pool by 56 % is the per-token cost, which
scales with the batch budget. "The pool is small because the model is large" is the wrong
diagnosis here.

**The default is already the cheap mode.** `thinking: false` changes throughput by less
than the run-to-run spread, because the default produces 41-token answers with no thinking
prelude. On the 0731 release the same switch was worth 3.5×. `reasoning_effort: low`, by
contrast, costs **40 % of the answers per second** and produces an answer of the same
visible length. [Measured](vllm-b12x/scenarios/reasoning-cost.md).

**This server cannot report its own reasoning share.** `completion_tokens_details` comes
back empty, so `reasoning_tokens` is unavailable and the protocol's reasoning column reads
0 % even when 146 tokens per answer produce no visible characters. Total token counts are
correct, so throughput is sound —
[how the split was recovered anyway](vllm-b12x/scenarios/reasoning-cost.md#reading).

**The kit ships a lower-case model name in its own helper scripts.** The server serves
`DeepSeek-V4-Flash`; `ready.sh`, `smoke.sh` and `mtp_accept.sh` ask for
`deepseek-v4-flash`. `ready.sh` runs to its timeout against a healthy server, and the other
two discard the failure.
[Details](vllm-b12x/README.md#pinned-values).

**The kit binds to `0.0.0.0` under `--network host`.** Its own README states the opposite
intent. Changed to `127.0.0.1` here before any measurement ran —
[what that costs a gateway](vllm-b12x/README.md#deviations-from-the-kit-as-shipped).

**Speculative decoding drafts two tokens per step, so acceptance length is
`1 + accepted/(drafted/2)`.** The kit's `mtp_accept.sh` divides by the draft count and
reported 1.65 where the correct figure is 2.29 — the reference run's per-position rates
(`1 + 0.727 + 0.432` = 2.16) are the same quantity computed correctly.

## References

- [`hikarioyama/dsv4-flash-nvfp4-sm120`](https://github.com/hikarioyama/dsv4-flash-nvfp4-sm120)
  — the kit: launch scripts, patches, and the published numbers verified here
- [`nvidia/DeepSeek-V4-Flash-NVFP4`](https://huggingface.co/nvidia/DeepSeek-V4-Flash-NVFP4)
  — checkpoint and model card
- [`deepseek-ai/DeepSeek-V4-Flash`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)
  — base model

## Still open

Each question is owned by the document that would answer it.

- [`--max-num-seqs` above 64](vllm-b12x/scenarios/concurrent-load.md#not-measured) — the
  single experiment that would explain the dip at concurrency 64, the 74 % spread and two
  cards that never saturate. Everything about the load picture is provisional until it runs
- [A batch budget between 512 and 2048](vllm-b12x/scenarios/concurrent-load.md#not-measured)
  — whether the larger KV pool is reachable without the workspace-lock crash
- [Long context at all](vllm-b12x/README.md#still-open) — the kit's 1M claim is
  capacity-verified only, and the configuration it needs is the one that fails under load.
  This is the largest untouched area
- [Answer quality under NVFP4](vllm-b12x/scenarios/single-stream.md#not-measured) — only
  speed was measured; whether the quantisation costs accuracy is untested
- [Why the KV pool is 11 % below the reference](vllm-b12x/README.md#the-kv-pool-is-set-by-the-batch-budget-not-by-vram)

Smaller gaps and the knobs deliberately dropped are in the
[setup README](vllm-b12x/README.md#still-open).
