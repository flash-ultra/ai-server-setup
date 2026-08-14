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
| [Concurrent load](scenarios/concurrent-load.md) | peak **14,657 total tok/s** at C=128 · 91–95 % GPU |
| [Long context](scenarios/long-context.md) | full 1M verified · prefill 470.7 s · **3/3 needles recovered** |

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

## Operation

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

- Warm 1M run to quantify the prefix-cache benefit; intermediate depths (256k, 512k)
  to map the prefill decay curve
- Lower `reasoning_effort` and measure the effect on throughput
- Run the correctness protocol: five cold starts under bursty load, to rule out draft
  corruption with confidence
- Re-profile the SPS cost table for this machine instead of using the shipped one
- Behaviour under real agent traffic — synthetic prompts overstate draft acceptance

---

*Measurements from 2026-08-14/15 · cloudscale GPU2-512-80-4-800 · SGLang v0.5.16 SM120 patchset*
