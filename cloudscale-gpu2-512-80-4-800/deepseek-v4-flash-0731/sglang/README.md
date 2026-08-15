# SGLang DSpark Production Stack

**DeepSeek-V4-Flash-0731 with tensor, data and expert parallelism on 4× RTX PRO 6000**

All four cards compute together at over 90 % utilisation, with the full 1M context
and working speculative decoding. In production since 2026-08-15.

**Machine:** [cloudscale.ch `GPU2-512-80-4-800`](../../README.md) ·
**Model:** [DeepSeek-V4-Flash-0731](../README.md)

| | |
|---|---|
| Engine | SGLang v0.5.16 + SM120 patchset |
| Image | `ghcr.io/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000` |
| Image size | 46 GB · 33 patches |
| Model | DeepSeek-V4-Flash-0731 (FP8 e4m3) |
| Parallelism | TP 4 · DP 4 · EP 4 |
| MoE backend | `flashinfer_mxfp4` |
| Speculation | DSPARK, block size 7 |
| KV cache | fp8_e4m3 · 2,799,872 tokens |
| Context | 1,048,576 (full) |
| VRAM | 86,989 MiB × 4 |
| Startup | 151 s warm · 274 s cold |

---

## Measured scenarios

| Scenario | Headline |
|---|---|
| [Single stream](scenarios/single-stream.md) | 131.2 output tok/s · 665.2 total tok/s · TTFT 0.15 s |
| [Concurrent load](scenarios/concurrent-load.md) | peak **27,026 total tok/s** at C=256 · curve still climbing · 97 % GPU |
| [Long context](scenarios/long-context.md) | full 1M verified · prefill 470.7 s · **3/3 needles recovered** |
| [Reasoning cost](scenarios/reasoning-cost.md) | thinking off = **3.5× answers/s**, 8.75× fewer tokens per answer |

---

## Why it runs at all

DeepSeek-V4 uses Manifold-Constrained Hyper-Connections. The corresponding DeepGEMM
kernel `tf32_hc_prenorm_gemm` does not exist for SM120 — every engine aborts with
`Assertion error: Unsupported architecture`. Tracked in
[DeepGEMM #317](https://github.com/deepseek-ai/DeepGEMM/issues/317) and
[vLLM #41063](https://github.com/vllm-project/vllm/issues/41063). Without SM120
kernels no forward pass completes.

> **The stack solves this with 33 backported patches.**
> Among them the Triton `hc_combine` kernel from PR #29927, which replaces the faulty
> mHC combine fallback, and an SM120 decode dispatch that pads non-bucket indices to
> the next CUTLASS size.

---

## Deployment

The compose file is not reproduced here — it comes from the
[upstream repository](https://github.com/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000)
(Apache 2.0, © 2026 Ombori) and carries per-flag rationale worth reading in the
original. Our deployment differs from their example in exactly **two lines**:

```bash
git clone https://github.com/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000 dsv4
cd dsv4 && cp docker-compose.example.yml docker-compose.yml

# 1. use the prebuilt image instead of building it locally
sed -i 's|image: sglang:v0.5.16-dsv4-sm120|image: ghcr.io/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000:latest|' docker-compose.yml

# 2. point the model mount at where the checkpoint actually lives
sed -i 's|- /models:/models:ro|- /mnt/scratch/models:/models:ro|' docker-compose.yml

docker compose up -d
```

The checkpoint is expected at `<mount>/DeepSeek-V4-Flash-0731` (~158 GB):

```bash
hf download deepseek-ai/DeepSeek-V4-Flash-0731 --local-dir /mnt/scratch/models/DeepSeek-V4-Flash-0731
```

The repository also ships `sps/dspark_sps_g7.json`, the profiled cost table the
compact verify path reads. Without it the scheduler degenerates to verify-all and the
speculative decoding configuration below does nothing.

### Running

```bash
docker compose up -d          # restart: unless-stopped
docker compose logs -f
docker compose down
```

| | |
|---|---|
| Direct | port 8000, OpenAI-compatible |
| Via litellm | port 4000 |
| Model name | `deepseek-v4-flash` |
| Sampling | temperature 1.0 · top_p 1.0 |

The sampling values are not optional: lower temperatures drive this checkpoint into
repetition loops.

### Configuration in effect

The flags below are what the container actually runs. Their reasoning is documented
inline in the upstream compose file; the ones that must not be changed are listed
under [pinned values](#pinned-values).

```
--tp-size 4 --dp-size 4 --enable-dp-attention --enable-dp-lm-head --ep-size 4
--context-length 1048576  --mem-fraction-static 0.85  --swa-full-tokens-ratio 0.1
--max-running-requests 256  --cuda-graph-max-bs 64
--kv-cache-dtype fp8_e4m3  --moe-runner-backend flashinfer_mxfp4
--speculative-algorithm DSPARK  --speculative-attention-mode decode
--speculative-dspark-block-size 7  --speculative-dspark-sps-table-path /sps/dspark_sps_g7.json
--disable-custom-all-reduce  --chunked-prefill-size 4096
--reasoning-parser deepseek-v4  --tool-call-parser deepseekv4
--default-chat-template-kwargs '{"thinking": true}'
--load-balance-method prefix_affinity  --prefix-affinity-fallback round_robin
--enable-prefill-delayer  --prefill-delayer-max-delay-passes 8
--prefill-delayer-token-usage-low-watermark 0.5
```

Environment, set by the same file:

```
SGLANG_OPT_DSV4_NONPAGED_INDEXER_MIN_QUERY_TOKENS=1024   # = chunked_prefill / dp_size
SGLANG_FP8_PAGED_MQA_LOGITS_TORCH=0
SGLANG_OPT_USE_TILELANG_INDEXER=0
SGLANG_OPT_DEEPGEMM_HC_PRENORM=1
SGLANG_RAGGED_VERIFY_MODE=compact
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

`--cuda-graph-max-bs 64` caps decode graphs **per DP rank**, which is why 256 global
running requests still stay on-graph at `--dp-size 4`. With `--dp-size 1` it would
need to be 64 global.

---

## What the configuration does

A first attempt with a different SM120 fork ran, but fell far short: 582 tok/s at 32
concurrent requests against 1571 here. Three differences explain the factor of 3.

### MoE backend

The first fork used `--moe-runner-backend triton`. This stack pins `flashinfer_mxfp4`
with an explicit rationale: *triton crashes, TensorRT-LLM corrupts FP4.*

### Parallelism

Instead of pure tensor parallelism, three axes run simultaneously:

```
--tp-size 4 --dp-size 4 --enable-dp-attention --enable-dp-lm-head --ep-size 4
```

DP attention quadruples KV capacity; expert parallelism distributes the 256 experts.

### Speculative decoding

DSpark was not active at all in the first attempt. Here it runs with a profiled cost
table and `--speculative-dspark-block-size 7`.

> **Draft depth 5 — the shipped default — corrupts output on SM120.**
> The cause was context aliasing in NCCL symmetric memory. It does not show up in
> single tests, only under varying load across several cold starts.

---

## Pinned values

These are conditions, not recommendations. Deviating causes crashes or silent
corruption.

| Setting | Value | Failure mode otherwise |
|---|---|---|
| flashinfer | 0.6.15.post1 | 0.6.16+ segfaults on CUDA-graph capture |
| DSpark depth | 7 | depth 5 corrupts output |
| MoE backend | `flashinfer_mxfp4` | triton crashes, trtllm corrupts FP4 |
| custom all-reduce | disabled | breaks graph capture |
| indexer threshold | 1024 | must equal `chunked_prefill / dp_size` |
| temperature / top_p | 1.0 / 1.0 | lower values cause repetition loops |

---

## Observations from operation

### 96 % of tokens are reasoning

With thinking enabled, almost the entire generation goes into the reasoning part — in
one test 253 reasoning tokens against 10 tokens of visible answer. This dominates cost
and capacity planning, and it is why a first measurement was off by a factor of 5: it
counted only the answer text.

Sending `chat_template_kwargs: {"thinking": false}` per request cuts cost per answer
by a factor of 8.75 and raises answers per second by 3.5×; `reasoning_effort` in
contrast changes almost nothing under load. Measured in
[reasoning-cost.md](scenarios/reasoning-cost.md).

### The reasoning parser works

Unlike the first fork, this stack separates cleanly: `content` holds the answer,
`reasoning_content` the thinking, with no `</think>` remnants in visible text.

### Latency grows with concurrency

Throughput rises up to 128 concurrent requests, but so does response time — from
3.8 s at one user to 29.8 s at 128. For interactive use the usable range is 32 to 64;
beyond that you are optimising for batch processing. Numbers in
[concurrent-load.md](scenarios/concurrent-load.md).

---

## Upstream issues worth tracking

- [SGLang #33422](https://github.com/sgl-project/sglang/issues/33422) — dsv4 prefill underperforming on SM120 with TP=4
- [SGLang #32311](https://github.com/sgl-project/sglang/issues/32311) — hang on 4× RTX 6000 Pro with limited host RAM

## References

- [ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000](https://github.com/ombori/deepseek-v4-flash-0731-sglang-4x-rtx-pro-6000) — patchset and image used here

---

## Still open

Configuration and correctness, owned here:

- Run the correctness protocol: five cold starts under bursty load, to rule out draft
  corruption with confidence. Depth 7 has held so far, but the failure mode of depth 5
  was precisely one that a single run does not show.
- Re-profile the SPS cost table for this machine instead of using the shipped one

Missing measurements are listed in the scenario they belong to:
[long context](scenarios/long-context.md#not-measured) ·
[concurrent load](scenarios/concurrent-load.md#not-measured) ·
[reasoning cost](scenarios/reasoning-cost.md#not-measured). Single stream has no
open items.

---

*Measurements from 2026-08-14/15 · cloudscale GPU2-512-80-4-800 · SGLang v0.5.16 SM120 patchset*
