# Scenario: long context — vLLM 0.28.0

Needle-in-a-haystack at the checkpoint's full context length.

**Setup:** [vLLM 0.28.0 TP=2](../README.md) · `nvidia/MiniMax-M2.5-NVFP4` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-08-30

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens 180000`
instead of the default 960,000, because the checkpoint's `max_position_embeddings` is
196,608. Everything else is pinned — filler calibrated against the server's own
tokeniser, three needles planted at 10 %, 50 % and 90 %.

The resulting prompt measured 180,108 tokens server-side.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Prefill (TTFT) | 69.8 s |
| Prefill throughput | 2580 tok/s |
| Total duration | 70.0 s |
| GPU utilisation | 100 % · 100 % |
| Needles recovered | **3 of 3** — see correction below |

## The harness reported 0 of 3; the model recovers all three

`bench.py` printed `0 of 3 []`. **That number is a harness artifact and must not be read
as a model property.** Two things gave it away: the run reports a total duration of 70.0 s
against a TTFT of 69.8 s, leaving 0.2 s for generation — too short for the ~200 tokens
the answer needs — and the recovered-needle list came back empty rather than partial.

Verified by replaying the **identical** prompt construction — same `FILLER`, same three
needle sentences at the same positions, same question text, 180,108 prompt tokens — with
one change, `stream=False`:

```
4.1s prompt=180108 completion=214 reasoning=196 finish=stop
gefunden=3/3 ['XR-4471', 'QT-8829', 'ZB-1503']
ANTWORT: '\n\nXR-4471, QT-8829, ZB-1503'
```

All three codes, **including the middle needle at 50 %**, which is the one this scenario
exists to test. A second, independent construction with different filler and a German
question also returned 3 of 3 at 173,518 prompt tokens.

The prefill figures above come from the harness run and are unaffected — TTFT is measured
before the stream breaks down. Only the needle row is replaced.

## What is wrong with the harness is not yet pinned down

`bench.py` uses `stream=True` for this scenario and accumulates `delta["content"]`. The
obvious explanation — that vLLM's `minimax_m2` reasoning parser routes the answer into
`delta["reasoning_content"]`, which the collector counts but does not store — was
**tested and does not hold**: a short streaming request against the same server produced
11 `delta.content` chunks and zero `delta.reasoning_content` chunks.

So the streaming path breaks somewhere else, most likely at the ~70 s mark under a
180k-token prefill. That is unresolved. Until it is, **`--scenario longctx` cannot be
trusted for this engine and model combination**, and its needle row should be verified
non-streaming before publication.

## Not measured

- **The root cause in `bench.py`.** Whether other `longctx` rows in this repository are
  affected has not been checked.
- **Needle recovery below full length.** Only 180k was tested.
- **Prefill throughput without prefix caching interference.** The verification run
  returned in 4.1 s because the prompt was already cached from the harness run; only the
  69.8 s figure describes a cold prefill.
