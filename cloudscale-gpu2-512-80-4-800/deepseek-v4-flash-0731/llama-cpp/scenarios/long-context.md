# Scenario: long context — llama.cpp

How the setup behaves as context depth grows. Measured to 128k of the configured
1,048,576.

**Setup:** [llama.cpp layer-split](../README.md) · DeepSeek-V4-Flash-0731 UD-Q8_K_XL ·
[cloudscale `GPU2-512-80-4-800`](../../../README.md) · measured 2026-08-14

## Method

`llama-bench`-style prompt-processing and generation runs at increasing context depth,
single stream, `-b 2048 -ub 512`. The batch-size series below repeats `pp4096` at empty
context and at 64k depth for five `-ub` values.

## Context decay

Prompt processing halves roughly every 64k tokens.

| Context depth | 0 | 16k | 64k | 128k |
|---|---|---|---|---|
| Prompt processing (tok/s) | 2638 | 1917 | 1135 | 736 |
| Generation (tok/s) | 54.6 | 51.6 | 46.0 | 41.7 |

Practical figure: a 13,463-token prompt takes **20.8 seconds** before the first token.
For long contexts this, not generation, is the dominant cost.

## Batch size at depth

The `-ub 8192` recommendation from the llama.cpp 1M-context thread was measured on a
single GPU with CPU offload. On four cards with everything in VRAM it reverses:

| `-ub` | pp4096 empty | pp4096 @ 64k | spread @ 64k |
|---|---|---|---|
| **512 (default)** | 2468 | **1319** | ± 0.05 |
| 1024 | 2726 | 1159 | ± 0.24 |
| 2048 | 2641 | 1135 | ± 0.19 |
| 4096 | 2641 | 1136 | ± 0.11 |
| 8192 | 2127 | 959 | ± 97.10 |

## Reading

**Generation holds up, prefill does not.** From empty to 128k, generation loses 24 %
while prompt processing loses 72 %. Any workload with long inputs is paying for
prefill, and speculative decoding does not help there.

**Measure at depth, not at zero.** At empty context `-ub 1024` looks like the best
choice; at 64k it is 12 % worse than the default. The ranking inverts, which is exactly
why the single-GPU advice does not transfer.

**8192 is also unstable.** A spread of ± 97 against ± 0.05 for the default — the large
ubatch does not just lose throughput, it makes the number unreliable. Leave
`-b 2048 -ub 512` alone.

## Not measured

- 1M context end to end — duration, stability, VRAM
- KV-cache dtypes `-ctk` / `-ctv` at depth
- `-ts` balance (VRAM is unevenly distributed at 41–47 GiB)

Worth knowing before running the full context: a 32-bit overflow at very long context
when `n_kv × n_ubatch` crosses 2³² was reported in llama.cpp as #24643, #24718 and
#24912, and fixed in #24706, #24776 and #24945.
