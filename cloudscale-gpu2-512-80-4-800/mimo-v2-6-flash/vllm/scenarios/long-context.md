# Scenario: long context — vLLM TP=4

**Setup:** [vLLM 0.33.0 TP=4](../README.md) · `MiMo-V2.6-Flash-RL` · [the four-card machine](../../../README.md) · measured 2026-11-06, 17:16–17:18

## Method

Protocol [`v1`](../../../../benchmark/README.md), `--scenario longctx --target-tokens 64000 / 128000 / 250000`,
filler calibrated against the server's tokeniser (20.0 tokens per sentence), needles at
10 / 50 / 90 %, thinking on, one streaming request per size on an idle engine.

## Result

<!-- protocol v1 · counted via usage fields -->

| Target | Prefill (TTFT) | Prefill throughput | Total | GPU | Needles |
|---|---|---|---|---|---|
| 64,000 | 10.5 s | **6,104 tok/s** | 10.8 s | 100 % × 4 | **3 of 3** |
| 128,000 | 26.3 s | **4,865 tok/s** | 26.6 s | 96 % × 4 | **3 of 3** |
| 250,000 | 70.2 s | **3,561 tok/s** | 70.6 s | 97–99 % | **3 of 3** |

**Every needle at every length, and the rate falls by 42 % from 64k to 250k.** Nine of the
48 layers attend over the full context, and their cost grows faster than the prompt. The
two-card series read 180k at 3,070 tok/s; four cards land around 4,200 at the same depth
by interpolation, 1.4× for twice the cards. Decode behind 64k: 132.8 tok/s, 7 % under the
short-prompt rate ([single-stream](single-stream.md)).

| Prefill tok/s on the four-card machine | 64k | 128k | 250k |
|---|---|---|---|
| Qwen3.8-Flash-Next IQ3_S · Strata | 16,967 | 20,639 | 21,873 |
| Qwen3.8-Flash-Next FP8 · vLLM | 7,591 | 7,782 | 7,840 |
| **MiMo-V2.6-Flash-RL FP8 · vLLM** | 6,104 | 4,865 | 3,561 |
