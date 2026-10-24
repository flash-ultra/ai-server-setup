# MiMo-V2.6-Flash-RL

Xiaomi's MiMo-V2.6-Flash-RL on both cards of
[cloudscale `GPU2-256-40-2-1600`](../README.md) — 2× RTX PRO 6000 Blackwell, sm120, no
NVLink. Tested 2026-10-13.

| | |
|---|---|
| Checkpoint | [`XiaomiMiMo/MiMo-V2.6-Flash-RL`](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL) |
| Size on disk | 165.5 GiB |
| Quantisation | FP8 |
| Declared architecture | `MiMoV2ForCausalLM` |
| Architecture actually loaded | **`MiMoV2OmniForCausalLM`** — multimodal |
| Native context | 1,048,576 — **served at 196,608** |
| Modality | text and images measured; audio encoder loads, untested |
| Thinking | on by default, **switchable** — two of five candidate keys work |

## Verdict

**It delivers more answers per second, at lower latency, than anything else measured on
this machine — and it does it with thinking on.** 46.05 answers/s at p50 5.74 s against
32.58 at 7.96 s for DeepSeek-0731 with thinking off, and 10.97 at 27.58 s for the same
setup with thinking on. One setup, [vLLM with the vendor image at TP=2](vllm/) — no fork,
no patchset. What it does not take is output tokens per second, where DeepSeek's thinking
arm stays ahead at 3,584, and prefill depth, where DeepSeek fills the same 180,000 tokens
2.3× faster.

| | Measured |
|---|---|
| Single stream | 114.3 output tok/s, p50 0.57 s, two runs 0.7 % apart |
| Peak under load | **46.05 answers/s at concurrency 256** (3,128.9 output tok/s), p50 5.74 s |
| Prefill, 180,000 tokens | 58.6 s, 3,070 tok/s |
| GPU utilisation | **100 % on both cards at every level of the ladder** |
| Needles at 180,000 tokens | 3 of 3 |
| Thinking | on throughout, at 21–22 % of tokens |

One thing has to travel with those numbers: the ladder **had not turned over at 256**.
Answers per second rose at every level and the median response was still under six
seconds at the top, so the ceiling in the table is the protocol's, not the model's.

**The context window was the other caveat and no longer is.** The first series ran at
49,152 because nothing larger would start. It now serves 196,608 — four times as much,
the same as MiniMax, three quarters of DeepSeek — at a throughput indistinguishable from
before. What unlocked it was not a quantisation or an offload but a profiling default;
[the setup README](vllm/README.md#a-cuda-graph-profiling-default-costs-three-quarters-of-the-context-window)
has the measurement.

## Measurements

| Setup | Scenarios |
|---|---|
| [`vllm/`](vllm/) | [single](vllm/scenarios/single-stream.md) · [concurrent](vllm/scenarios/concurrent-load.md) · [long context](vllm/scenarios/long-context.md) · [reasoning cost](vllm/scenarios/reasoning-cost.md) |

## Against the other models on this machine

At concurrency 256, with every row's thinking state stated:

| | MiMo-V2.6-Flash | [DeepSeek-0731](../deepseek-v4-flash-0731/) | DeepSeek-0731 | [MiniMax-M2.5](../minimax-m2-5/) |
|---|---|---|---|---|
| Thinking | **on** | **on** | off (default) | on, not switchable |
| Answers/s | **46.05** | 10.97 | 32.58 | 9.75 |
| Output tok/s | 3,128.9 | **3,583.8** | 1,173.2 | 2,947.3 |
| Latency p50 | **5.74 s** | 27.58 s | 7.96 s | 57.34 s |
| Tokens/answer | 68 | 327 | 35 | 258 |
| Context served | 196,608 | 262,144 | 262,144 | 196,608 |
| Prefill at 180k | 3,070 tok/s | 7,133 tok/s | 7,133 tok/s | 2,580 tok/s |

**Against the like-for-like arm it is 4.2× the answers at a fifth of the latency.**
DeepSeek keeps the output-tokens-per-second column, and the tokens-per-answer column says
why: 327 against 68, four fifths of it scratchpad. More tokens per second is not more
work done.

**It also beats DeepSeek's thinking-*off* arm while thinking** — 46.05 against 32.58
answers/s, 5.74 s against 7.96 s. That is the comparison that settles whether the gap is
an artefact of the thinking state. It is not.

**What it gives up is prefill depth.** DeepSeek fills 180,000 tokens at 7,133 tok/s
against 3,070 here — 2.3× faster, and nearly flat from 64k upward where MiMo's rate falls
with depth. For one long document per request that is the column that matters, and it is
the opposite workload to the one above.

## Quality checks outside the protocol

**None of this is protocol `v1`.** The protocol measures throughput and says nothing about
whether answers are right. These checks were run because throughput alone could not
justify a switch; their method is stated here because there is no shared one to point at.

**Method.** Single requests against the running server through the OpenAI-compatible
endpoint, thinking on (the default), `max_tokens` 512 unless noted, answers checked
against values computed independently. No sampling-temperature control, no repeats except
where stated. This is a pass/fail battery, not a benchmark score.

| Battery | Items | Result |
|---|---|---|
| Everyday reasoning | 8 | **8/8** |
| Multi-step calculation | 8 | **8/8** |
| Adversarial / trick questions | 8 | **8/8** |
| Repeat consistency (one Bayes item, 3×) | 3 | **3/3 identical** |
| Needle in a haystack, 180,000 tokens | 3 | **3/3** |
| Vision on a synthetic image | 6 | **6/6** |

The quality batteries other than the needle run were measured on the earlier 49,152
configuration and were not repeated. The weights and the sampling path are unchanged, so
they are reported as they stand; a quality difference from the window change is not
expected and not ruled out.

The adversarial set was the one chosen to fail it: bat-and-ball, harmonic mean against
the arithmetic trap, −20 % followed by +20 %, the five-machines scaling question, a Bayes
item whose intuitive answer is an order of magnitude off (**1.94 %**), the birthday
problem (**50.7 %**), the look-and-say continuation (**312211**), and the wine-and-water
exchange (equal, and it said why). It took none of the bait.

**One real limit, and it is a configuration one.** `C(256,8)` — 409,663,695,276,000 —
came out correct, but only with `max_tokens` above 2,000. At 512 the thinking block
consumed the budget and `content` came back **empty**, not wrong. A client that pins
`max_tokens` low will see blank answers to hard questions rather than bad ones.

**Vision, and what the 6/6 does not cover.** The image was a PNG generated on the VM from
scratch — zlib stream and CRC chunks by hand, since there is no PIL there — showing four
red squares, two blue circles and the digits `4731`. The model counted both shapes,
read the digits, named the colours, got the spatial relation right and described the
whole image. An image costs roughly 250 prompt tokens. **Simple synthetic geometry is the
easy end of vision**; photographs, screenshots and document scans were not measured here.
The operator reports good results dumping real images and PDFs at it, which is not a
measurement in this repo.

## Model-specific gotchas

All three are documented with their failure modes in the
[setup README](vllm/README.md#pinned-values); the short form:

- **The `cu129` image the model card names does not build here.** `#error "DeepGEMM SM120
  kernels require CUDA 13.0 or newer"`, and because the kernels compile at launch it fails
  minutes in, not at pull time. Use `…-cu130`.
- **`thinking: false` — the DeepSeek key — is accepted and silently ignored.** So is
  `enable_thinking` as a top-level field. The working keys are
  `chat_template_kwargs: {"enable_thinking": false}` and `reasoning_effort: "none"`.
- **The declared architecture is not the one that loads.** `config.json` says
  `MiMoV2ForCausalLM`, which in vLLM's registry is text-only; the engine resolves
  `MiMoV2OmniForCausalLM` from the vision and audio configs in the same file. Reading the
  registry before downloading predicts the wrong class.
