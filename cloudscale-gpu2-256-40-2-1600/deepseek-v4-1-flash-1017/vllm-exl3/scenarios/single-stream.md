# Scenario: single stream — vLLM + EXL3, TP=2

One request at a time, no competing load. The interactive single-user case.

**Setup:** [vLLM + EXL3 plugin, TP=2](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3
3 bpw · [cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-25

## Method

Protocol [`v1`](../../../../benchmark/README.md), no deviations. `bench.py --scenario
single`, run **on the machine against the engine on `127.0.0.1:8010`**, not through the
`api-router` — a Python hop in front would be in the number.

Measured on the [measurement configuration](../README.md#two-configurations-and-which-numbers-belong-to-which):
the pack's 1,048,576-token window, 4.25 GiB of KV, `--max-num-seqs 8`, nothing else on
the cards. **The thinking switch was verified first**, as the protocol requires:
`chat_template_kwargs: {thinking: false}` takes `reasoning_tokens` from 18 to 0, and
three other plausible keys do not — see the
[probe table](../../README.md#model-specific-gotchas).

**One run.** The decode measurement below is two.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Output | **136.5 tok/s** |
| Total, incl. reasoning | 1159.5 tok/s |
| Requests | 0.82 req/s |
| Latency p50 | **1.19 s** |
| Tokens per answer | 165 (**75 %** reasoning) |
| GPU utilisation | 97 % · 96 % |

**The highest `v1` single-stream figure on this machine**, ahead of
[MiniMax](../../../minimax-m2-5/vllm/scenarios/single-stream.md) at 122.4 and
[MiMo](../../../mimo-v2-6-flash/vllm/scenarios/single-stream.md) at 113.9–114.7, from a
3-bit quantisation of a 763 B model.

## Decode rate, measured separately

`v1` reports output tokens over a 40 s window, which mixes prefill into the figure. A
streaming request measures the two apart: tokens after the first, divided by
`duration − TTFT`. 1500 tokens, the length the
[machine table](../../../README.md#per-stream-one-request-at-a-time) uses.

| | completion tokens | TTFT | Decode |
|---|---|---|---|
| run 1 | 1500 | 0.24 s | **114.2 tok/s** |
| run 2 | 1500 | 0.22 s | **128.4 tok/s** |

**A 12 % spread between two identical runs — the widest of any model measured here.**
Every other model on this machine reproduces its decode rate to within 0.5 %. The cause
is speculative decoding: the DSpark drafter proposes five tokens per step and how many
survive depends on what is being written, not on how fast the hardware is.

Acceptance over the single-stream run, from the engine's own `SpecDecoding` metrics:

| Window | Mean acceptance length | Acceptance rate |
|---|---|---|
| first 10 s | 4.57 of 5 | **71.4 %** |
| settled, 40 s on | 3.03–3.15 | 40.7–43.1 % |

**The opening window is not representative.** Acceptance starts near the drafter's
ceiling and falls by a third once the answer leaves its warmed-up preamble. A decode
figure taken from the first few seconds of a speculative stack overstates it by the same
third — which is one way two honest benchmarks of this model end up far apart.

## Why the pack's own decode figure is higher

The pack reports 224 tok/s single-stream decode. Both numbers are honestly measured and
they are not the same measurement:

| | the pack's figure | this one |
|---|---|---|
| Workload | agentic session replay | pinned `v1` prompt |
| Drafter | `DS41_DRAFTER=code` at `SPEC_K=7` | released drafter at `k=5`, the default |
| Measured over | a full session | 1500 tokens |

Code and tool-call traffic is the drafter's best case — repetitive, highly predictable
tokens — and the code-tuned head is the one the author pairs with it. `v1` deliberately
pins a single general-purpose prompt so that figures across engines and models stay
comparable, and that prompt is a worse case for speculation than agentic replay.
**Neither number transfers to the other's workload**, and the gap between them is a
property of speculative decoding rather than a disagreement about the hardware.

## Against the rest of the machine

| concurrency 1, thinking on | this setup | [DS-0731](../../../deepseek-v4-flash-0731/) | [MiMo](../../../mimo-v2-6-flash/) | [MiniMax](../../../minimax-m2-5/) | [Qwen 27 B](../../../qwen3-8-27b/) |
|---|---|---|---|---|---|
| `v1` output tok/s | **136.5** | 75.3–75.5 | 113.9–114.7 | 122.4 | 51.9 |
| Decode at 1500 | 114.2–128.4 | 95.0–95.1 | **118.4–118.7** | 116.6–116.7 | 48.6–49.0 |
| Latency p50 | 1.19 s | **0.47 s** | 0.56 s | 1.96 s | 3.84 s |

**First on the window figure, inside the leading band on decode, third on latency.**
The p50 is where thinking shows: 75 % of a default answer here is scratchpad, so the
user waits for 165 tokens where DeepSeek-0731 waits for 35.

**The `v1` column reads higher than decode, which should be impossible** — window
throughput carries one prefill per answer and must sit below the decode rate. The same
inversion appears on [MiniMax](../../../minimax-m2-5/vllm/scenarios/single-stream.md)
and has the same cause: decode slows as the KV cache grows inside one request, so a rate
measured over 1500 tokens is below the rate over the ~165 that this model actually
produces per answer. It is an argument for stating the generation length with every
decode figure, which is why the machine table's column header carries one.
