# Scenario: single stream — vLLM B12X

One request at a time, measured two ways because the two answer different questions.

**Setup:** [vLLM B12X TP=2](../README.md) · `nvidia/DeepSeek-V4-Flash-NVFP4` ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-17

## Method

Two tools, two numbers, and they are not interchangeable.

**Protocol `v1`, `--scenario single`.** The pinned prompt is ~1216 tokens and asks for a
three-sentence summary, so answers come back at **40 tokens**. At that length the
time-to-first-token dominates the wall clock, and the resulting tokens per second is a
*request-shaped* figure.

**The kit's `mtp_stream.py`, 1000 tokens, streaming.** Reports TTFT separately and
computes `(completion_tokens - 1) / (last_token_time - first_token_time)` — the pure
inter-token rate with prefill excluded. This is the number speculative decoding moves,
and the one the kit's own claims are stated in. Three runs, `max_tokens 1000`.

Both count via `usage`. Cards 2 and 3 were idle; the Infinity embedding container on
card 2 was still running for these runs and does not touch cards 0–1.

## Protocol `v1`

| Metric | Value |
|---|---|
| Output | 97.8 tok/s |
| Total (prompt + output) | 3041.7 tok/s |
| Requests | 2.42 req/s |
| Latency p50 | 0.41 s |
| Tokens per answer | 40 |
| GPU | 79 % · 83 % · 0 % · 0 % |

## Decode rate and TTFT

| Run | TTFT | Decode | e2e | Wall for 1000 tokens |
|---|---|---|---|---|
| 1 | 184.6 ms | 163.0 tok/s | 158.3 tok/s | 6.32 s |
| 2 | 192.8 ms | 159.3 tok/s | 154.7 tok/s | 6.46 s |
| 3 | 173.0 ms | 159.8 tok/s | 155.7 tok/s | 6.42 s |

## MTP acceptance

Read from `/metrics` after the three streaming runs plus three 400-token requests, over
`vllm:spec_decode_num_accepted_tokens_total` and `vllm:spec_decode_num_draft_tokens_total`.

| | Value |
|---|---|
| Accepted | 708 |
| Drafted | 1096 |
| Draft acceptance | **64.6 %** |
| Mean acceptance length | **2.29** |

## Reading

**97.8 and 159 tok/s are both correct and measure different things.** The `v1` answer is
40 tokens long, so 173–193 ms of prefill sits in front of ~250 ms of decode; the
request-shaped rate lands near 93–98 tok/s no matter how fast decoding is. Quoting the
`v1` figure as this model's generation speed understates it by 40 %, and quoting the
decode rate as its request throughput overstates what a short-answer workload gets. The
[concurrent-load sweep](concurrent-load.md) is the number that describes a served
workload.

**The kit's published single-stream claims reproduce, slightly better.** Against the
reference run's 197.8 ms TTFT, 155.6 tok/s decode and 58.0 % acceptance, this machine
measures 173–193 ms, 159.3–163.0 tok/s and 64.6 %. Nothing here needed tuning to get
there — it is the kit's own configuration.

**The kit's acceptance-length arithmetic is wrong for this configuration.**
`mtp_accept.sh` prints `1 + accepted/drafted`, which holds only when one token is drafted
per step. The spec config draws **two** (`num_speculative_tokens: 2`), so the divisor is
the step count, not the draft count: `1 + 708/(1096/2)` = 2.29, where the script prints
1.65. The reference run's per-position rates confirm the corrected form —
`1 + 0.727 + 0.432` = 2.16 is the same quantity, computed the same way.

## Not measured

- Whether the 64.6 % acceptance holds on prompt shapes other than prose. The kit reports
  58 % on diverse text against 94 % on a repeat-this-sentence prompt, so the figure is
  known to be text-dependent and this measurement uses a single prose prompt
- Answer quality against the BF16 checkpoint. Only speed was measured; whether the
  NVFP4 quantisation costs accuracy on this hardware is untested here
- MTP off as a control on this machine. The kit publishes 108.8 tok/s without
  speculation against 150.6 with it (+38 %); reproducing that split would cost an
  18-minute restart and was not run
