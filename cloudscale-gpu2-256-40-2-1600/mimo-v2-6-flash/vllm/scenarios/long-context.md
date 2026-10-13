# Scenario: long context — vLLM, MiMo build

Needle-in-a-haystack at 180,000 tokens.

**Setup:** [vLLM TP=2](../README.md) · `MiMo-V2.6-Flash-RL` ·
[cloudscale `GPU2-256-40-2-1600`](../../../README.md) · measured 2026-10-13

## Method

Protocol `v1`, `--scenario longctx`, **with one deviation**: `--target-tokens 180000`
instead of the default 960,000. 180,000 is the depth the other models on this machine
were measured at, so this row is directly comparable to them.

The served window is 196,608. An
[earlier configuration of this same setup](../README.md#a-cuda-graph-profiling-default-costs-three-quarters-of-the-context-window)
served 49,152 and was measured at 44,000; those figures are superseded and not carried
forward.

## Result

<!-- protocol v1 · max_tokens 512 · 40 s/level · 3 warmup requests discarded · counted via usage fields -->

| Metric | Value |
|---|---|
| Prompt | 1.26 MB, 9,000 sentences at 20.00 tokens each, needles at 10/50/90 % |
| Prefill (TTFT) | 58.6 s |
| Prefill throughput | **3,070 tok/s** |
| Total duration | 59.2 s |
| GPU utilisation | **100 % · 100 %** |
| Needles recovered | **3 of 3** `['XR-4471', 'QT-8829', 'ZB-1503']` |

## Reading

**All three needles at the same depth as the other two models**, middle one included.
That is the one the scenario exists to test: a model attending only to the edges recovers
the outer two and loses the one at 50 %.

| at 180,000 tokens | Prefill | Needles |
|---|---|---|
| [DeepSeek-0731](../../../deepseek-v4-flash-0731/sglang/scenarios/long-context.md) | 7,133 tok/s | 3/3 |
| **MiMo-V2.6-Flash** | **3,070 tok/s** | **3/3** |
| [MiniMax-M2.5](../../../minimax-m2-5/vllm/scenarios/long-context.md) | 2,580 tok/s | 3/3 |

**Prefill is where this setup gives ground.** DeepSeek is 2.3× faster filling the same
context. Where MiMo leads — answers per second under load, by 4.2× against DeepSeek's
thinking arm — is in [concurrent load](concurrent-load.md), and the two are different
workloads: one long document against many short requests.

**At shallower depth the same setup measured 7,436 tok/s** (44,000 tokens, earlier
configuration). The rate therefore falls with depth here, which is the opposite of
DeepSeek, whose prefill is nearly flat from 64k to 180k. Whether that is the hybrid
attention or the smaller KV pool is unmeasured.

**Both cards saturated throughout.** Prefill is the compute-heavy phase and the one where
tensor parallelism pays.

## Not measured

- **Depths between 44,000 and 180,000.** The curve is anchored at two points from two
  different configurations, which is not a curve.
- **Anything past 196,608**, the served window. The engine estimates the ceiling at
  198,208.
- **Warm prefill.** This was the first long request the server saw.
