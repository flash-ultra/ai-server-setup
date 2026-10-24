# vLLM, vendor MiMo build — MiMo-V2.6-Flash-RL on two cards

The image the model card points to, unmodified. Tested 2026-10-13.

| | |
|---|---|
| Engine | vLLM, `vllm/vllm-openai:mimo-v26-x86_64-cu130`, 30.7 GB |
| Checkpoint | [`XiaomiMiMo/MiMo-V2.6-Flash-RL`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) — 165.5 GiB, FP8 |
| Cards | 2 of 2 (TP=2) |
| Resolved architecture | **`MiMoV2OmniForCausalLM`** |
| Context served | 196,608 of 1,048,576 native |
| KV cache | 3.9 GiB · 197,494 tokens · max concurrency 1.00× at full context |
| Memory in use | 92,645 MiB per card of 97,887 |
| Time to `/health` 200 | 120–150 s |

## Configuration in effect

```
--model /model --served-model-name cyberlink
--host 127.0.0.1 --port 8000
--tensor-parallel-size 2 --trust-remote-code
--gpu-memory-utilization 0.98 --max-model-len 196608
--reasoning-parser mimo --tool-call-parser mimo --enable-auto-tool-choice
```

Environment: `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0`.
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
| `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS` | **`0`** | left at the default, available KV drops from 3.9 GiB to 2.36 GiB and the longest window that starts is 54,528 — a quarter of what the same hardware serves with it off. Measured below |
| `--max-model-len` | `196608` | `262144` aborts: 4.59 GiB of KV needed against 3.9 GiB available. The engine's own estimate at that point is 198,208, so the ceiling sits just above the configured value |
| `--gpu-memory-utilization` | `0.98` | at `0.97` with the profiler off the window still reaches 131,072 but not beyond; at `0.95` KV falls to 0.45 GiB. The weights are 82.8 GiB per card |
| `--override-generation-config` | **`{"max_new_tokens": 32768}`** | without it the checkpoint's own `generation_config.json` caps every reply at **2,048 tokens**. vLLM applies that file's defaults when the client sends no `max_tokens`, so answers stop mid-sentence with `finish_reason: length` and no error anywhere. Measured: 8,435 characters and `length` before, 12,366 and `stop` after, same prompt |
| `--reasoning-parser` | `mimo` | without it the thinking block is not separated and `reasoning_tokens` stays empty |
| thinking switch | **`enable_thinking`** | `thinking`, the DeepSeek-V4 key, is **accepted and silently ignored** — verified below, not assumed |

## A CUDA-graph profiling default costs three quarters of the context window

The window was 49,152 for the first series. Raising it failed the same way every time —
`Available KV cache memory: 2.36 GiB` — and the figure did not move between 131,072 and
262,144, so it was not the window that was eating the memory.

The log says what is: `--gpu-memory-utilization=0.9700 is equivalent to 0.9637 without
CUDA graph memory profiling`. Setting `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0` and
`0.98` together:

| | before | after |
|---|---|---|
| Available KV | 2.36 GiB | **3.9 GiB** |
| Longest window that starts | 54,528 | **198,208** (engine estimate) |
| Configured | 49,152 | **196,608** |

**A 65 % gain in KV memory bought a 4× window.** The relationship is not linear, and the
next section says why.

## A token gets cheaper as the window grows

The two configurations side by side, same model, same cards:

| | 49,152 window | 196,608 window |
|---|---|---|
| Available KV | 6.33 GiB | 3.9 GiB |
| KV pool | 135,191 tokens | **197,494 tokens** |
| Bytes per token | 49.1 KiB | **25.4 KiB** |
| Max concurrency | 2.75× | 1.00× |

**The pool is 46 % larger on 38 % less memory.** A token costs exactly half as much at the
larger window. The same ratio shows up in the engine's own failure messages: 3.18 GiB
needed at 131,072 but only 4.59 GiB at 262,144, where a linear cache would need 6.36.

That signature — a fixed component plus a linear one — is hybrid attention: part of the
layers carry a sliding window that saturates once the context passes its width, while the
rest keep growing. Below the window width every layer stores in full, which is the
expensive regime the first series was measured in.

**The practical consequence is counterintuitive: asking for more context can cost less
memory per token.** A capacity estimate extrapolated from a short-window measurement will
be wrong by a factor of two on this checkpoint.

## `--kv-cache-dtype fp8` is accepted and does nothing

Halving the KV cache looked like the obvious route to a larger window. It is not available
here, and the engine does not say so.

| at `--max-model-len 131072` | KV needed | engine's max-length estimate |
|---|---|---|
| default dtype | 3.18 GiB | 54,528 |
| `--kv-cache-dtype fp8` | **3.18 GiB** | **54,528** |

Identical to the digit. The flag produces no error, no warning, and no effect — the same
failure shape as the thinking keys below, one level down in the stack. Anyone reaching for
fp8 KV on this checkpoint should check the engine's own cache figures rather than assume
the dtype took.

## The checkpoint caps replies at 2,048 tokens and nothing says so

Code generation stopped mid-function. The cap is not in the engine's configuration, the
gateway, or the client — it ships with the weights:

```json
// generation_config.json
{ "max_new_tokens": 2048, "temperature": 1.0, "top_p": 0.95, ... }
```

vLLM reads that file and uses its values whenever the request omits `max_tokens`. Same
prompt, no `max_tokens`, before and after `--override-generation-config`:

| | characters | `finish_reason` | completion tokens |
|---|---|---|---|
| default | 8,435 | **`length`** | 2,048 |
| overridden to 32,768 | **12,366** | **`stop`** | 3,224 |

With thinking on the gap is wider still: 7,993 characters against 54,034.

**DeepSeek-V4-Flash's `generation_config.json` has no `max_new_tokens` field**, which is
why the truncation appeared only after switching models and looked like a gateway
problem. Prefer `--override-generation-config` over `--generation-config vllm`: the
latter also discards the checkpoint's recommended `top_p` and `do_sample`.

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
| [long context](scenarios/long-context.md) | measured at 180,000 tokens |
| [reasoning cost](scenarios/reasoning-cost.md) | measured — the key was verified first |
