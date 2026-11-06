# Scenario: single stream — vLLM TP=4

One request at a time, no competing load. Both thinking arms, plus the decode rate
measured apart from prefill.

**Setup:** [vLLM 0.33.0 TP=4, Docker](../README.md) · `Qwen3.8-Flash-Next-FP8` ·
[the four-card machine](../../../README.md) · measured 2026-11-06

## Method

Protocol [`v1`](../../../../../dist/benchmark/README.md), no
deviations. `bench.py --scenario single` on the machine against `127.0.0.1:8000`. The model
is alone on the cards at `--gpu-memory-utilization 0.90`. The thinking switch was verified
first: `enable_thinking: false` takes `reasoning_tokens` from 44 to 0
([smoke test](../README.md#pinned-values)). One run per arm. The decode table is
`decode.py`: one streaming
request, tokens after the first divided by duration minus TTFT, `min_tokens` for the
1,500-token rows.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** (default) | thinking **off** |
|---|---|---|
| Output | **110.4 tok/s** | 97.9 tok/s |
| Total, incl. prompt | 773.5 tok/s | 2513.3 tok/s |
| Requests | 0.53 req/s | **1.98 req/s** |
| Latency p50 | 1.86 s | **0.49 s** |
| Tokens per answer | 210 (**78 %** reasoning) | 50 (0 %) |
| GPU utilisation | 99 % on all four | 99 % on all four |

**Decode, measured separately**

| | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 200 / 188 | 0.11 / 0.10 s | **115.7 / 115.8 tok/s** |
| thinking off, run 1 / 2 | 54 / 45 | 0.09 / 0.09 s | **115.7 / 115.7 tok/s** |
| thinking on, 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.09 / 0.10 s | **114.8 / 114.6 tok/s** |
| thinking on, behind a 64k prompt | 273 | 7.61 s | **113.1 tok/s** |

Decode is a flat **115 tok/s** whatever the answer length or arm, and loses 2 % behind
64k of context. The 110 and 98 tok/s of the protocol rows are that rate minus the
per-request overhead of a 1.3k-token prompt and a short answer.

## Against Strata on the Rocky two-card machine (2× RTX PRO 4500)

The same model as a 3-bit GGUF on two 32 GB cards, with its MTP draft layer in use
(Strata single stream):

| | vLLM FP8, 4× RTX PRO 6000 | Strata IQ3_S, 2× RTX PRO 4500 |
|---|---|---|
| Output, thinking on | 110.4 | **141.4** |
| Output, thinking off | 97.9 | **108.5** |
| Decode | 115 | **136–150** |
| Prefill at 64k | **7591** | 5957 |

**Without its MTP head, vLLM loses the single stream to the small machine by 1.3×.** The
reason is not the cards: Strata drafts with the model's 4 B MTP layer and accepts about
70 % of the drafts, while the run above decodes one token per step.

## With the MTP head: `--speculative-config qwen4_exp_mtp`, 2 draft tokens

Same container, restarted with
`--speculative-config '{"method":"qwen4_exp_mtp","num_speculative_tokens":2}'` (vLLM
warns the name is deprecated in favour of `mtp`, and that more than one draft token
re-runs the single MTP layer). Ready after 250 s; the KV pool shrinks to 3,088,943 tokens.
Measured 11:53–12:02.

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | thinking **on** | thinking **off** | vs. no draft |
|---|---|---|---|
| Output | **175.4 tok/s** | **132.4 tok/s** | +59 % / +35 % |
| Requests | 0.85 req/s | 2.65 req/s | |
| Latency p50 | 1.25 s | 0.36 s | 1.86 / 0.49 s |
| Tokens per answer | 206 (79 % reasoning) | 50 | |

| Decode, measured separately | completion tokens | TTFT | Decode |
|---|---|---|---|
| thinking on, run 1 / 2 | 203 / 215 | 0.11 / 0.10 s | **174.6 / 172.2 tok/s** |
| thinking off, run 1 / 2 | 53 / 46 | 0.10 / 0.09 s | **178.0 / 168.8 tok/s** |
| thinking on, 1,500 tokens, run 1 / 2 | 1500 / 1500 | 0.10 / 0.10 s | **181.8 / 163.3 tok/s** |
| thinking on, behind a 64k prompt | 157 | 7.88 s | **191.3 tok/s** |

The engine's own counter during the run: **mean acceptance length 2.06** of a possible 3,
accepted 472 of 892 drafted tok/s. **Decode goes from a flat 115 to 163–192 tok/s, the
single stream from 110 to 175.** That is 1.24× the Strata single stream on the Rocky two-card machine (2× RTX PRO 4500),
with the better checkpoint. Under load the draft is worth nothing, see
[concurrent-load](concurrent-load.md#with-the-mtp-head).
