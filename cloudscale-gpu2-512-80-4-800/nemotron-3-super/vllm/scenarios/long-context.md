# Scenario: long context — Nemotron-3-Super, one copy

**Setup:** [vLLM 0.33.0, four copies](../README.md) · [the four-card machine](../../../README.md) · measured 2026-11-07, 18:18–18:19

One request reaches one copy, so every number here is **one card**.

| Target | Prefill (TTFT) | Prefill throughput | Needles |
|---|---|---|---|
| 64,000 | 7.9 s | 8,101 tok/s | **3 of 3** |
| 128,000 | 15.9 s | 8,043 tok/s | **3 of 3** |
| 250,000 | 37.9 s | 6,597 tok/s | **3 of 3** |

**One card reads as fast as four cards do for Qwen3.8-Flash-Next under vLLM** (7,591–7,840
tok/s). Every needle found; decode behind 64k unchanged at 86.9 tok/s.
