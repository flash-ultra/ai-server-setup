# Scenario: single stream — llama.cpp master

One request at a time, no competing load.

**Setup:** [llama.cpp `-sm layer`](../README.md) ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md)

Two configurations of the same setup have been measured. They are listed side by side
because the quantisation step is the comparison this table exists to support.

| | Quantisation | Slots | Measured |
|---|---|---|---|
| **A** | UD-Q5_K_XL | 1 | 2026-08-31 |
| **B** | UD-Q6_K_XL | 1 | 2026-09-21 |

## Method

Protocol `v1`, `--scenario single`, no deviations, both configurations.

**`max_tokens` is pinned at 512, and this model does not always finish inside it.** On a
separate image question, budgets of 300 and 2500 both returned empty `content` with the
budget spent; 8000 produced the answer. Part of what this table counts is therefore
truncated thinking, not a finished reply.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | A · Q5_K_XL | B · Q6_K_XL |
|---|---|---|
| Output | 88.5 tok/s | 86.6 tok/s |
| Total (incl. reasoning) | 656.8 tok/s | 686.5 tok/s |
| Requests | 0.45 req/s | 0.47 req/s |
| Latency p50 | 2.22 s | 2.01 s |
| Tokens per answer | 197 (0 % reasoning) | 182 (0 % reasoning) |
| GPU utilisation | 46 % · 45 % | 45 % · 44 % |
| Time to listening | ~9 s | 13.4 s |

## Reading

**A higher bit depth costs 2.1 % of output throughput here.** Q6_K_XL carries 6.9 % more
weight than Q5_K_XL — 157.5 against 147.4 GiB — and gives up 88.5 → 86.6 tok/s for it.
That is not the trade a bandwidth-bound decoder would make. It follows from the
[45 % ceiling](../../../README.md#llamacpp-cannot-split-across-these-cards): with half the
machine idle at every level, there is slack to absorb the extra weight reads, and the
extra precision is close to free.

**Do not read the latency and requests columns as a Q6 win.** p50 is 2.01 s against
2.22 s, but the answers are also shorter — 182 against 197 tokens. Output tokens per
second is the comparable column; the other two follow answer length.

**2.0–2.2 s for a complete answer is the case this model is good at.** It is the
interactive single-user number, and it is the only column where this setup is
competitive:
[DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/single-stream.md) is at
0.47 s but answers in 35 tokens; this one writes ~190.

**45 % on both cards, with a single request in flight.** Nothing else is running. That is
`-sm layer` alternating between the cards, and it is the same number the
[concurrency ladder](concurrent-load.md) shows at every level and in every slot
configuration.

**0 % reasoning is "not reported".** llama.cpp omits the field. ~190 tokens for a
three-sentence summary is not a model that skipped thinking.

## Not measured

- **Decode rate with prefill excluded.**
- **Variance.** One run per configuration.
- **Quality difference between Q5 and Q6.** Only throughput was compared. Whether the
  extra bit depth changes answers was not tested, and it is the reason to prefer Q6 —
  the throughput argument alone does not justify a re-download.
