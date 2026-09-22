# llama.cpp master — Qwen3.8-Flash-Next on two cards

Upstream llama.cpp, built for sm120. First measured 2026-08-31, reconfigured 2026-09-21.

| | |
|---|---|
| Engine | llama.cpp `master`, built from source |
| Image | `llamacpp-sm120:master`, built from [`provisioning/Dockerfile.llamacpp-sm120`](https://github.com/flash-ultra/ai-server-setup) |
| Checkpoint | `unsloth/Qwen3.8-Flash-Next-GGUF`, 6 shards + `mmproj-F16.gguf` |
| Cards | 2 of 2, `-sm layer` |

**Support is upstream, no patch needed** — unlike GLM-5.3-Flash, which still requires an
open draft PR. The publisher's instruction is plain "use llama.cpp".

## Two configurations

Both were measured under protocol `v1`. **B is the configuration this setup is kept
at**; which model occupies the cards at any moment is a separate question, and only one
large model fits at a time.

| | Quantisation | `-c` | `--parallel` | Context per slot | VRAM after load |
|---|---|---|---|---|---|
| **A** | UD-Q5_K_XL | 262,144 | 1 | 262,144 | 60,065 / 55,415 MiB |
| **B** | UD-Q6_K_XL | 1,572,864 | 6 | 262,144 | 87,055 / 81,773 MiB |

A is kept because every number published before 2026-09-21 was measured on it.
The move from A to B changed two things at once — bit depth and slot count — so the two
effects were separated before switching: see
[single stream](scenarios/single-stream.md) for the quantisation step at one slot, and
[concurrent load](scenarios/concurrent-load.md) for the slot sweep at fixed
quantisation.

## Configuration in effect

```
-m /models/UD-Q6_K_XL/Qwen3.8-Flash-Next-UD-Q6_K_XL-00001-of-00006.gguf
--mmproj /models/mmproj-F16.gguf
--image-min-tokens 1024
-ngl 999 -sm layer -c 1572864 --parallel 6
--host 127.0.0.1 --port 8000 --alias cyberlink --jinja
```

Container started with `--restart unless-stopped`. Time to listening 13.4 s at Q6 with
warm page cache, against ~9 s at Q5.

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| `-sm` | `layer` | `row` is rejected by the CUDA backend on these cards — the reason utilisation pins at 45 % |
| `-c ÷ --parallel` | **≤ 262,144** | that is `max_position_embeddings`, and the checkpoint carries no `rope_scaling`. A larger per-slot budget runs past what the model was trained for, without an error at load |
| `--parallel` | `6` | at `1`, p50 is 33.7 s at 16 concurrent requests against 13.1 s here — roughly double at every level from 8 upward. It does not change the throughput ceiling, only how fast the server reaches it. Above 6 the KV pool no longer fits beside the Q6 weights |
| `--mmproj` | `mmproj-F16.gguf` | without it the server loads the text half only and refuses images |
| `--image-min-tokens` | `1024` | the load log warns that Qwen-VL needs at least 1024 image tokens for grounding; without it a 640×360 probe arrives as 288 tokens |
| `--jinja` | set | required for the checkpoint's chat template |

## How much context fits

Measured on configuration B's checkpoint by starting the server at four context sizes and
reading `nvidia-smi` directly after load:

| `-c` | `--parallel` | Card 0 | Card 1 |
|---|---|---|---|
| 32,768 | 1 | 59,453 MiB | 54,181 MiB |
| 262,144 | 1 | 65,551 MiB | 60,303 MiB |
| 1,048,576 | 4 | 78,441 MiB | 73,169 MiB |
| 1,572,864 | 6 | 87,055 MiB | 81,773 MiB |

**KV cost per token is not constant.** From 32,768 to 262,144 tokens card 0 grows by
6,098 MiB, which is 0.0266 MiB per token. From 262,144 to 1,048,576 it grows by
12,890 MiB, which is 0.0164 MiB per token — 38 % less. Sizing a larger pool by
extrapolating from a small one therefore overestimates the cost; a projection from the
first pair put `-c 1048576` at 89,100 MiB against the 78,441 MiB actually used.

At configuration B, 10,832 MiB remain free on card 0 and 16,114 MiB on card 1.

## Weights on disk are 34.6 GiB larger than weights in VRAM

| | File | VRAM after load | Difference |
|---|---|---|---|
| UD-Q5_K_XL | 147.4 GiB | 112.8 GiB | **−34.6 GiB** |
| UD-Q6_K_XL | 157.5 GiB | 122.9 GiB | **−34.6 GiB** |

The increment matches the file increment exactly — 10.1 GiB in both columns — while the
absolute gap is identical across two quantisations. It is systematic, not a reading
error, and it is not the KV cache: both rows are at `-c 262144 --parallel 1`.

It is also not resident in the process. With the server loaded, RSS is 19.1 GiB and the
host reports 12 GB used against 219 GB in buff/cache. That is consistent with expert
tensors being served from the mmap'd file through the page cache rather than copied to
VRAM, which would also explain why `-ngl 999` does not put the full file on the cards.

**Unconfirmed.** This build does not log its per-buffer allocation at default verbosity,
so the placement was not read out directly. Treat the mechanism as a hypothesis and the
34.6 GiB as a measurement.

## Building it

The Dockerfile fetches a **tarball** rather than cloning. From inside a build container,
`git clone https://github.com/ggml-org/llama.cpp` fails reproducibly:

```
fatal: could not read Username for 'https://github.com': No such device or address
fatal: expected flush after ref listing
```

The same clone succeeds on the host, and cloning a different repository from inside a
container succeeds too — so it is neither Docker nor GitHub in general. The tarball
download over the same connection works. Cause unconfirmed; rate limiting on the public
address is the suspicion, not a finding.

The `libcuda.so.1` stub link and the `/etc/ld.so.conf.d` entry are both required; without
the latter the container exits immediately with
`error while loading shared libraries: libllama-server-impl.so`.

## Scenarios

| Scenario | Status |
|---|---|
| [single stream](scenarios/single-stream.md) | measured on A and B |
| [concurrent load](scenarios/concurrent-load.md) | measured on A (two runs) and B, plus a slot sweep |
| [long context](scenarios/long-context.md) | measured on A only |
| reasoning cost | **not measured** — no thinking key verified, and an unverified key produces a false negative |

## Still open

- **`GGML_CUDA_FA_ALL_QUANTS` is off** in this build, so a quantised KV cache is not
  available. It roughly doubles build time and was not needed here.
- **Long context on configuration B.** The 3-of-3 needle result at 180k was measured on
  A. Six slots change the KV layout, so it does not carry over untested.
- **Where the 34.6 GiB live.** Rebuilding with a verbose load log, or a build that prints
  per-buffer allocation, would settle it.
- **What sets the ~1,400 output tok/s ceiling.** Both configurations flatten there at
  about 42 % GPU, so it is not the slot count — that was measured, not assumed. Whether
  it is llama.cpp's scheduler or the layer split itself cannot be separated on these
  cards, because `-sm row` does not load.
