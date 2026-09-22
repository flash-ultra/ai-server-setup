# Scenario: long context — SGLang TP=2

Needle-in-a-haystack at three depths, and 180k twice.

**Setup:** [SGLang TP=2](../README.md) · `DeepSeek-V4-Flash-0731` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30 and 2026-09-22

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens` is set
explicitly instead of the default 960,000. 180,000 is the value
[MiniMax-M2.5 was measured at](../../../minimax-m2-5/vllm/scenarios/long-context.md), so
the two stay directly comparable; 64,000 and 128,000 were added on 2026-09-22 to map the
curve between them. None of these is a limit of the checkpoint — it serves 262,144 here
and is native to 1,048,576.

The 2026-09-22 runs went against a server started 20 minutes earlier and were the first
long-context requests it saw, so no prefix cache from a previous depth was in play.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Depth | Prompt | Prefill (TTFT) | Prefill tok/s | Total | GPU | Needles |
|---|---|---|---|---|---|---|
| 64,000 | 0.45 MB | 7.8 s | **8227** | 8.0 s | 100 % · 100 % | **3 of 3** |
| 128,000 | 0.90 MB | 17.1 s | **7480** | 17.3 s | 99 % · 96 % | **3 of 3** |
| 180,000 | 1.26 MB | 25.2 s | **7133** | 25.5 s | 98 % · 97 % | **3 of 3** |
| 180,000 *(2026-08-30)* | 1.26 MB | 26.4 s | 6823 | 26.6 s | 99 % · 99 % | **3 of 3** |

Needles are `['XR-4471', 'QT-8829', 'ZB-1503']` at 10 %, 50 % and 90 % of the prompt in
every run.

## Reading

**Prefill decays gently with depth.** 8227 → 7480 → 7133 tok/s while the prompt grows
2.8×, a loss of 13 % across the range. Time to first token is close to linear in depth —
7.8, 17.1, 25.2 s — which is what a flat throughput curve implies and is the useful form
for planning: roughly **1 second of prefill per 7,000 tokens** anywhere in this range.

**The 180k measurement reproduces after 23 days**, on a different server process, to
within 4.5 % on time and 4.6 % on throughput. The second run came out faster, not slower.

**2.6× the prefill throughput of MiniMax-M2.5** on the same cards and the same prompt:
7133–6823 against 2580 tok/s, 25 s against 69.8 s to first token. For agent work with a
large standing context, that is the difference between a pause and a coffee break.

**All three needles at every depth, middle one included**, which is the one the scenario
exists to test. Retrieval does not degrade between 64k and 180k.

**The harness worked here, and that is itself a finding.** The same scenario against
MiniMax under vLLM reported
[0 of 3 and had to be corrected by hand](../../../minimax-m2-5/vllm/scenarios/long-context.md#the-harness-reported-0-of-3-the-model-recovers-all-three).
Under SGLang the streaming path returns the answer intact. **That narrows the open
`bench.py` bug to the vLLM combination** rather than to the scenario or to long prompts in
general — which was not knowable from a single engine.

## Not measured

- **The full 1M context.** `max_total_num_tokens` is 1,382,912, so one 1M request fits the
  pool arithmetically, but `--context-length` is set to 262,144 — reaching it needs a
  restart, not just a longer prompt. Concurrency would drop to one. Untested.
- **Between 180k and 262,144**, the actual served ceiling. The curve is mapped only to
  180k, and whether it stays flat to the top of the served window is unknown.
- **Warm prefill.** Every run here was the first request at its depth. What a repeated
  query against the same context costs — the prefix-cache benefit — is unmeasured, and it
  decides whether the 25 s is a one-off or a per-query cost.
