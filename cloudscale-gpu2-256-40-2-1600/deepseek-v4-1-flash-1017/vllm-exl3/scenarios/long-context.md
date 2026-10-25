# Scenario: long context — vLLM + EXL3, TP=2

Needle-in-a-haystack at 180,000 and at 960,000 tokens.

**Setup:** [vLLM + EXL3 plugin, TP=2](../README.md) · `DeepSeek-V4.1-Flash-1017` EXL3
3 bpw · [cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-25

## Method

Protocol [`v1`](../../../../benchmark/README.md), `bench.py --scenario longctx`, run
twice with `--target-tokens` at 180,000 and 960,000. Filler is calibrated against the
server's own tokeniser — 20.00 tokens per sentence here — and three codes are planted at
10 %, 50 % and 90 % of the prompt. **The middle needle is the actual test**: a model that
only attends to the edges returns the outer two and misses it.

Measured on the [measurement configuration](../README.md#two-configurations-and-which-numbers-belong-to-which),
whose window is the pack's full 1,048,576 tokens with a 1,071,558-token KV pool. The
180,000 depth matches the one
[every other model here was measured at](../../../README.md#per-stream-one-request-at-a-time)
so the prefill figures line up; 960,000 exists because no model on this machine had ever
been taken near a million.

**One run per depth.**

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Depth | Prompt | Prefill (TTFT) | Prefill tok/s | Total | GPU | Needles |
|---|---|---|---|---|---|---|
| 180,000 | 1.26 MB | 15.8 s | **11,386** | 16.0 s | 96 % · 98 % | **3 of 3** |
| 960,000 | 6.72 MB | 105.2 s | 9,123 | 105.4 s | 93 % · 92 % | **3 of 3** |

## Reading

**Three of three needles at 960,000 tokens** — by a factor of four the deepest verified
retrieval in this repository, against Qwen3.8-27B's 240,000. The middle needle came back
at both depths.

**11,386 tok/s of prefill is the fastest on this machine by 1.6×**, ahead of
DeepSeek-V4-Flash-0731 at 7,133 on the same prompt depth:

| | Prefill tok/s at 180k | ratio to this setup |
|---|---|---|
| **this setup** | **11,386** | — |
| [DeepSeek-V4-Flash-0731](../../../deepseek-v4-flash-0731/) | 7,133 | 0.63 |
| [Qwen3.8-27B](../../../qwen3-8-27b/) | 4,207 | 0.37 |
| [MiMo-V2.6-Flash](../../../mimo-v2-6-flash/) | 3,070 | 0.27 |
| [MiniMax-M2.5](../../../minimax-m2-5/) | 2,580 | 0.23 |
| [Qwen3.8-Flash-Next](../../../qwen3-8-flash-next/) | 1,343 | 0.12 |

**From the largest checkpoint in the comparison.** 763 B total parameters, 6 of 384
experts active, 3 bits per weight. The machine's
[active-parameter finding](../../../../README.md#active-parameter-count-predicts-prefill-speed-not-parameter-count)
held across a 10× parameter spread; this row extends it to 28× and in the same
direction. Prefill cost tracks what is read per token, and three-bit experts are cheap
to read.

**Prefill decays by only 20 % across a 5.3× increase in depth**, 11,386 to 9,123.
Qwen3.8-27B, the only other model here measured at more than two depths, loses 26 % over
a 3.75× range.

**A million-token request costs about two minutes before the first token**, and
generation afterwards is free: 0.2 s of the 105.4 s total. Any client in front of this
needs its timeout set from the prefill. At the served window of 327,680 the same
arithmetic gives roughly 30 s.

**GPU utilisation drops slightly at the deepest point**, 96–98 % at 180k against
93–92 % at 960k. What the cards wait on was not isolated — this setup keeps the Engram
tables and the coldest experts in pinned host RAM and reads them over PCIe, so host
transfers are the obvious candidate, but nothing here measures that directly.
