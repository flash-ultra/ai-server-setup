# llama.cpp Layer-Split

**DeepSeek-V4-Flash-0731 as GGUF on 4× RTX PRO 6000 Blackwell**

Stable in operation and strong for single users — with a hard, measured ceiling
under load. Superseded as of 2026-08-15; retained as a fallback.

**Machine:** [cloudscale.ch `GPU2-512-80-4-800`](../../README.md) ·
**Model:** [DeepSeek-V4-Flash-0731](../README.md)

| | |
|---|---|
| GPU | 4× RTX PRO 6000 Blackwell Max-Q, 389,007 MiB total |
| Driver | 595.71.05 · sm120 (compute capability 12.0) |
| llama.cpp | `7e4c0a96` · 2026-08-14 |
| CUDA | 13.0.1 / nvcc V13.0.88 |
| Compiler | gcc 13.3.0 |
| Model | DeepSeek-V4-Flash-0731 UD-Q8_K_XL |
| Size | 150.75 GiB · 284.33 B params |
| Experts | 256 (non-REAP), 6 active |
| Startup | 20 s (warm page cache) |

---

## Measured scenarios

| Scenario | Headline |
|---|---|
| [Single stream](scenarios/single-stream.md) | **91 tok/s** with DSpark vs 54.9 without · TTFT 0.05 s |
| [Concurrent load](scenarios/concurrent-load.md) | working range up to C=16 · TTFT jumps to 13.71 s at C=32 |
| [Long context](scenarios/long-context.md) | prompt processing halves roughly every 64k tokens |

---

## Deployment

Both files sit next to this README: [`Dockerfile`](Dockerfile) and
[`docker-compose.yml`](docker-compose.yml).

```bash
# build for sm120 only — under two minutes on 80 cores
docker build --build-arg LLAMA_COMMIT=$(git ls-remote \
    https://github.com/ggml-org/llama.cpp.git HEAD | cut -f1) \
    -t llamacpp-sm120:local .

docker compose up -d          # restart: unless-stopped
docker compose logs -f
```

Expects the GGUF conversion and the DSpark draft model under the mounted directory:

```bash
hf download unsloth/DeepSeek-V4-Flash-0731-GGUF \
    --local-dir /mnt/scratch/models/DSv4-GGUF --include "*UD-Q8_K_XL*"
```

The build identity is readable from the image itself:
`docker run --rm llamacpp-sm120:local cat /build-info.txt`

### Configuration in effect

```
-m   DeepSeek-V4-Flash-0731-UD-Q8_K_XL-00001-of-00005.gguf
-md  dspark-DeepSeek-V4-Flash-0731-Q8_0.gguf
--spec-type draft-dspark  --spec-draft-n-max 3
-ngl 99   -ngld 99   -sm layer
-c 1048576   -np 8              → 8 slots × 131,072 tokens
-fa on   --jinja
--temp 1.0  --top-p 1.0  --min-p 0.01
--metrics  --host 0.0.0.0  --port 8000
```

Batch sizes are deliberately absent — the defaults `-b 2048 -ub 512` measured optimal
and overriding them costs up to 38 % at depth. See
[long-context.md](scenarios/long-context.md).

For a single request with the full 1M context, set `-np` to 1; `-c` is the shared KV
pool, divided across the slots.

### Build gotcha

Inside a CUDA `devel` image the driver stub must be linked explicitly, otherwise
linking fails with `undefined reference to cuMemCreate`. `libcuda.so.1` ships with the
driver, not the toolkit — the stub is link-time only, at runtime the container gets the
real library from the host:

```bash
ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1

cmake -B build -G Ninja \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=120 \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA_FA_ALL_QUANTS=ON \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64/stubs"
```

One more: the image has no `curl`, so a compose healthcheck must use `python3`.

---

## The ceiling: no tensor parallelism

> **Only `-sm layer` loads this model.**
> `-sm row` and `-sm tensor` both fail with `failed to load model` — even with a
> self-built sm120 binary. llama.cpp has no tensor parallelism for DeepSeek-V4.

The cause is architectural: `attention.head_count_kv = 1`. Multi-head Latent
Attention has a single KV head, which cannot be split across four cards. In
layer-split mode the layers sit sequentially on the GPUs — a token walks through
them one card at a time while the other three wait.

This shows up in utilisation: **11–14 % per card, regardless of load.** Four cards
at 14 % is roughly one saturated GPU. The other three contribute memory, not
compute. No parameter changes this.

---

## Speculative decoding

> **DSpark is the single largest win in this setup.**
> 91 instead of 55 tok/s at short context, draft acceptance 64–69 %.

For the 0731 checkpoint there is **no MTP**, only DSpark — as documented in the
corresponding llama.cpp merge. That merge also states `--spec-draft-n-max 1` is often
optimal and values above 2 show regressions; this setup runs 3. Untested, and the
obvious next measurement.

---

## Disproven assumptions

Both sound plausible and are measurably wrong — recorded here so nobody
reintroduces them.

### Large batches hurt

The `-ub 8192` recommendation comes from a llama.cpp thread on 1M context, but was
measured on a single GPU with CPU offload. On four cards with everything in VRAM it
reverses:

| `-ub` | pp4096 empty | pp4096 @ 64k | spread @ 64k |
|---|---|---|---|
| **512 (default)** | 2468 | **1319** | ± 0.05 |
| 1024 | 2726 | 1159 | ± 0.24 |
| 2048 | 2641 | 1135 | ± 0.19 |
| 4096 | 2641 | 1136 | ± 0.11 |
| 8192 | 2127 | 959 | ± 97.10 |

At filled context — the normal operating case — the default beats 2048 by 16 % and
8192 by 38 %, and measures far more stably. Leave `-b 2048 -ub 512` alone.

### Static linking changes nothing

The Unsloth guide builds with `BUILD_SHARED_LIBS=OFF`. Measured head to head:
pp512 2110 vs 2096, pp2048 2335 vs 2330, tg128 54.96 vs 55.01. Every difference sits
inside the measurement spread.

---

## Why the measurement series was cut short

> **This setup is no longer in production.** The SGLang stack took over on
> 2026-08-15. llama.cpp remains configured and runnable as a fallback.

A full optimisation sweep was planned: threads, KV-cache dtypes, `-ts` balance,
DSpark tuning, and the 1M-context verification. It was stopped once a comparison
stack on identical hardware was available.

The reason is the magnitude of the gap. Both setups measured with the same load test
— requests per second and latency are independent of how tokens are counted:

| Concurrent | llama.cpp req/s | SGLang req/s | llama.cpp TTFT | SGLang TTFT |
|---|---|---|---|---|
| 1 | 0.42 | 0.62 | 0.05 s | 0.15 s |
| 8 | 1.10 | 2.12 | 0.24 s | 0.18 s |
| 16 | 1.40 | 3.83 | 0.31 s | 0.20 s |
| 32 | 1.73 | **5.55** | **13.71 s** | **0.25 s** |
| 64 | — | 7.95 | — | 0.32 s |

At 32 concurrent requests the comparison stack delivers **3.2× the requests** at
**55× lower latency**, running at 80–94 % GPU utilisation instead of 20 %.

Further tuning would not have changed that ordering. The remaining knobs — threads,
KV-cache dtype, tensor balance — move things by single-digit percentages while the
gap is a factor of 3 to 55. Measurement time went into building the faster stack
instead of refining the slower one.

---

## Still open

Two gaps still matter, because they decide whether the fallback is trustworthy on the
day it is needed. Both are owned by the scenario that would close them:

- [`--spec-draft-n-max` 1 vs 3](scenarios/single-stream.md#not-measured) — the merge
  notes call 1 often optimal and report regressions above 2; this setup runs 3
- [1M context end to end](scenarios/long-context.md#not-measured) — verified only to
  128k, while the server is configured for the full 1,048,576

### Not planned

Dropped for the reason given above: they move single-digit percentages against a gap
of a factor 3 to 55.

- `--threads` (default 80) against smaller values
- KV-cache dtypes `-ctk` / `-ctv`
- `-ts` balance (VRAM is unevenly distributed at 41–47 GiB)
- `-np` above 8 — whether more slots move the TTFT cliff at concurrency 32, or only
  spread the same starved compute across more queues

These are listed so nobody re-derives them as fresh ideas. If this setup ever returns
to production, they are the place to start.

---

## What this setup is still good for

As a fallback it remains valuable: it starts in 20 seconds rather than two and a half
minutes, needs no 46 GB image distribution, carries no 33 applied patches, and runs on
a plain upstream commit. For single-user work, for testing against a known reference,
or if the SGLang stack fails, it is back within minutes.

---

## Upstream issues worth tracking

- [llama.cpp #26965](https://github.com/ggml-org/llama.cpp/issues/26965) — DeepSeek-V4-Flash tokenizer crashes on long tool output
- 32-bit overflow at very long context when `n_kv × n_ubatch` crosses 2³² (reported as #24643, #24718, #24912; fixed in #24706, #24776, #24945)

## References

- [unsloth/DeepSeek-V4-Flash-0731-GGUF](https://huggingface.co/unsloth/DeepSeek-V4-Flash-0731-GGUF) — GGUF conversion used here
- [llama.cpp "one million tokens prompt club"](https://github.com/ggml-org/llama.cpp/discussions/24622) — long-context reports

---

*Measurements from 2026-08-14 · cloudscale GPU2-512-80-4-800 · llama.cpp 7e4c0a96*
