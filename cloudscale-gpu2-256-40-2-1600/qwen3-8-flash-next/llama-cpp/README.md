# llama.cpp master — Q5_K_XL on two cards

Upstream llama.cpp, built for sm120. Tested 2026-08-31.

| | |
|---|---|
| Engine | llama.cpp `master`, built from source |
| Image | `llamacpp-sm120:master`, built from [`provisioning/Dockerfile.llamacpp-sm120`](https://github.com/flash-ultra/ai-server-setup) |
| Checkpoint | `unsloth/Qwen3.8-Flash-Next-GGUF` UD-Q5_K_XL, 6 shards + `mmproj-F16.gguf` |
| Cards | 2 of 2, `-sm layer` |
| Context served | 262,144, one slot |
| Memory in use | 60,065 / 55,415 MiB of 97,887 each |
| Time to listening | ~9 s with warm page cache |

**Support is upstream, no patch needed** — unlike GLM-5.3-Flash, which still requires an
open draft PR. The publisher's instruction is plain "use llama.cpp".

## Configuration in effect

```
-m /models/UD-Q5_K_XL/Qwen3.8-Flash-Next-UD-Q5_K_XL-00001-of-00006.gguf
--mmproj /models/mmproj-F16.gguf
--image-min-tokens 1024
-ngl 999 -sm layer -c 262144 --parallel 1
--host 127.0.0.1 --port 8000 --alias cyberlink --jinja
```

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| `-sm` | `layer` | `row` is rejected by the CUDA backend on these cards — the reason utilisation pins at 45 % |
| `--mmproj` | `mmproj-F16.gguf` | without it the server loads the text half only and refuses images |
| `--image-min-tokens` | `1024` | the load log warns that Qwen-VL needs at least 1024 image tokens for grounding; without it a 640×360 probe arrives as 288 tokens |
| `--jinja` | set | required for the checkpoint's chat template |

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
| [single stream](scenarios/single-stream.md) | measured |
| [concurrent load](scenarios/concurrent-load.md) | measured, two runs |
| [long context](scenarios/long-context.md) | measured |
| reasoning cost | **not measured** — no thinking key verified, and an unverified key produces a false negative |

## Still open

- **`GGML_CUDA_FA_ALL_QUANTS` is off** in this build, so a quantised KV cache is not
  available. It roughly doubles build time and was not needed here.
- **Q6_K_XL untried**, though 40 GB per card sat unused.
- **`--parallel` above 1 untried.** One slot held the full context; more slots would
  divide it.
