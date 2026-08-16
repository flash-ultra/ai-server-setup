# Gemma-4-31B

Dense Gemma-4 on a single RTX PRO 6000 under llama.cpp. Tested 2026-08-16.

| | |
|---|---|
| Checkpoint | [`google/gemma-4-31B-it`](https://huggingface.co/google/gemma-4-31B-it) |
| Weights used | `unsloth/gemma-4-31B-it-GGUF` BF16 — 46.5 + 10.7 GB |
| Architecture | `gemma4`, dense |
| Context | 256 K native; measured at 32,768 |
| Speculation | MTP, `gemma4-assistant`, 0.9 GB |
| VRAM | 82,129 MiB of 97,887 |

## Verdict

**Choose the sparse sibling instead.** On the same card, engine and configuration,
[Gemma-4-26B-A4B](../gemma-4-26b-a4b/) delivers 2.6× the output tokens at concurrency 32
and 3.9× better median latency, at a comparable total parameter count. Nothing measured
here favours the dense variant.

Its one distinguishing property is capacity pressure: at 82 GB it leaves 15 GB of card,
against 42 GB for the sparse model — which is what makes context sizing tight rather than
comfortable.

## Measurements

| Setup | Scenarios |
|---|---|
| [`llama-cpp/`](llama-cpp/) | [single](llama-cpp/scenarios/single-stream.md) · [concurrent](llama-cpp/scenarios/concurrent-load.md) · [reasoning](llama-cpp/scenarios/reasoning-cost.md) |

## Model-specific gotchas

**`-c 65536` does not fit.** The KV cache alone wants 38.4 GB on top of 57 GB of weights,
and the process exits at load with `cudaMalloc failed: out of memory`. 32,768 is what
runs, and `-c` ÷ `-np` must still exceed prompt plus `max_tokens`.

**The thinking switch is `enable_thinking`**, as on the sparse sibling; the protocol
default `thinking` is accepted and ignored, and `reasoning_effort` is inert.

**Turning thinking off buys nothing here.** Tokens per answer fall 12×, answers per
second do not move at all, and utilisation drops to 13 %. With a ~1000-token prompt and a
36-token answer the request is prefill-bound. The identical switch is worth 2.6× on the
sparse sibling — the saving only materialises where decode was the limit.

## Still open

- [The stall between 8 and 16 concurrent](llama-cpp/scenarios/concurrent-load.md#not-measured)
  — throughput flat at 230–238 output tok/s while latency goes from 16 s to 41 s; whether
  more slots move it was not tried
- Whether the engine comparison run for the sparse sibling reproduces here. Only
  llama.cpp was measured for this model

### Not planned

- **SGLang and vLLM for this model.** The
  [engine comparison](../gemma-4-26b-a4b/engine-comparison.md) was run on the sparse
  variant, which is the one worth serving; repeating it here would measure a model
  nobody would deploy on this hardware
