# vLLM, vendor MiMo build — MiMo-V2.6-Flash-RL on two cards

The image the model card points to, unmodified. Tested 2026-10-13.

| | |
|---|---|
| Engine | vLLM, `vllm/vllm-openai:mimo-v26-x86_64-cu130`, 30.7 GB |
| Checkpoint | [`XiaomiMiMo/MiMo-V2.6-Flash-RL`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) — 165.5 GiB, FP8 |
| Cards | 2 of 2 (TP=2) |
| Resolved architecture | **`MiMoV2OmniForCausalLM`** |
| Context served | 49,152 of 1,048,576 native |
| KV cache | 6.33 GiB · max concurrency 2.75× at full context |
| Memory in use | 94,013 MiB per card of 97,887 |
| Time to `/health` 200 | 120–150 s |

## Configuration in effect

```
--model /model --served-model-name cyberlink
--host 127.0.0.1 --port 8000
--tensor-parallel-size 2 --trust-remote-code
--gpu-memory-utilization 0.97 --max-model-len 49152
--reasoning-parser mimo --tool-call-parser mimo --enable-auto-tool-choice
```

Container started with `--restart unless-stopped`.

## The checkpoint declares a text architecture and gets loaded as a multimodal one

`config.json` says `architectures: ["MiMoV2ForCausalLM"]`. In vLLM's registry that name maps
to `mimo_v2.py`, whose class is `nn.Module, SupportsPP, MixtureOfExperts, SupportsEagle3` —
**no `SupportsMultiModal`**. The multimodal class lives in `mimo_v2_omni.py` under a
different registry key.

Reading the registry alone therefore predicts a text-only load. The engine does not do
that: it resolves to `MiMoV2OmniForCausalLM`, evidently from the `vision_config` and
`audio_config` present in the same file.

**The lesson generalises: the architecture string is what you check before downloading,
but it does not settle which implementation runs.** That is only visible in the startup
log.

## Pinned values

| Setting | Value | What happens otherwise |
|---|---|---|
| Image tag | **`…-cu130`** | the `cu129` tag the model card names fails at startup: `#error "DeepGEMM SM120 kernels require CUDA 13.0 or newer"`. The kernels are compiled at launch, so this surfaces minutes in, not at pull time |
| `--max-model-len` | `49152` | at `131072` the engine aborts: 3.18 GiB of KV needed against 2.36 GiB available. At the default (native 1,048,576) only 0.45 GiB is available and the engine's own estimate drops to 3,792 tokens |
| `--gpu-memory-utilization` | `0.97` | at `0.95`, KV falls to 0.45 GiB. The weights are 82.8 GiB per card; what the vision and audio encoders plus CUDA graphs take out of the remainder is most of it |
| `--reasoning-parser` | `mimo` | without it the thinking block is not separated and `reasoning_tokens` stays empty |
| thinking switch | **`enable_thinking`** | `thinking`, the DeepSeek-V4 key, is **accepted and silently ignored** — verified below, not assumed |

## Thinking can be switched off, and only two of five ways work

Same prompt, five variants, counted via `usage`:

| Variant | completion tokens | reasoning tokens |
|---|---|---|
| default | — | active |
| `chat_template_kwargs {"enable_thinking": false}` | 66 | **0** |
| `reasoning_effort: "none"` | 47 | **0** |
| `reasoning_effort: "low"` | 57 | 24 |
| `chat_template_kwargs {"thinking": false}` | 98 | 31 — **no effect** |
| `enable_thinking` as a top-level field | 94 | 42 — **no effect** |

The two that fail are the interesting ones. Neither produces an error; both return a
normal answer with thinking still on. A `reasoning` scenario run with the wrong key would
have reported "disabling thinking changes nothing", which is the false negative the
[protocol](../../../benchmark/README.md) warns about.

## Scenarios

| Scenario | Status |
|---|---|
| [single stream](scenarios/single-stream.md) | measured |
| [concurrent load](scenarios/concurrent-load.md) | measured |
| [long context](scenarios/long-context.md) | measured at 44,000 tokens |
| [reasoning cost](scenarios/reasoning-cost.md) | measured — the key was verified first |

## Still open

- **The actual context ceiling.** 49,152 was chosen conservatively, below the 54,528 the
  engine estimated while failing at 131,072. That estimate was computed from the 2.36 GiB
  free in *that* configuration; at 49,152 there are 6.33 GiB free, so the real ceiling is
  higher. Narrowing it costs one restart per probe and was not done, because every
  measurement in this directory would then have to be repeated.
- **Audio.** The model accepts it and the engine loads the encoder. Nothing was sent.
- **Images.** Same: the capability is loaded, no image was measured.
- **CPU offload.** This build exposes `--cpu-offload-gb`, `--kv-offloading-size` and
  `--kv-offloading-backend`. With 230 GB of host RAM idle, offloading KV is the obvious
  route to a larger context. Untested, and the only local reference point for PCIe
  streaming is the [FreeToken trial](../../trials/freetoken.md), where it cost about half
  the throughput.
