# Strata 0.2.11, DeepSeek engine — DeepSeek-V4.1-Flash-1017 GSQ-RCO 2.25 bpw on four cards

Set up 2026-11-06 with `setup.sh --family deepseek41 --model ISTA-DAS-2.25bpw --gpus all
--vision gpu --context 262144`. The DeepSeek path is a separate engine, `strata-dsv41`,
that setup downloads as a prebuilt package (`0.1.57-linux-x86_64-cuda-cuda13`, 445 MB) from
Strata's signed update feed; nothing was compiled.

| | |
|---|---|
| Engine | `strata-dsv41` 0.1.57 (from Project Maya's `maya-ds4`), served by Strata 0.2.11's `server.py` |
| Files | four-shard IQ2_XS set (155 GB), Engram IQ4_NL (111 GB), DSpark drafter Q8_0 (8 GB); 275 GB downloaded in 8 minutes |
| Cards | 4 of 4, **layer split, `DS4_SPLIT=10,10,10,10`** — tensor parallelism is refused ("the experts' 256-value blocks split n_ff 2304 no other way") |
| Experts | all 15,744 in VRAM, 37–43 GB per card; 0 on the CPU |
| Host RAM | 141 GB in use; the RAM store reads the 13,099 hottest experts (119.8 GB) in 12 s at start |
| Draft | DSpark, `--dspark auto --dspark-conf 0.65` |
| Slots | 8 (`--parallel 8`) |
| Start to ready | **45 s** |
| API | port 8080, model name `deepseek-v4.1-flash`; thinking text in `reasoning_content`, no `reasoning_tokens` in `usage` |

```
strata-dsv41 --serve --pack …/packs/deepseek-v4.1-flash-ist-das-2.25bpw --max-context 262144
  --eos 1 --vision on --dspark auto --dspark-conf 0.65 --tp 2 --reserve-mib 900
server.py --engine strata --config strata-deepseek-v4.1-flash-ist-das-2.25bpw.json --port 8080 --parallel 8
DS4_SPLIT=10,10,10,10
```

## The automatic layer split, and how to override it

The engine picks the contiguous split that streams the fewest experts from RAM into its
busiest card. When everything fits, every split scores zero and the search keeps the first
one it finds. Here that was:

| Card | Layers, automatic | Experts | Free | Layers, `DS4_SPLIT=10,10,10,10` | Experts | Free |
|---|---|---|---|---|---|---|
| 0 | 0 (+ drafter) | 10.7 GB | 83 GB | 0–9 (+ drafter) | 43.1 GB | 50 GB |
| 1 | 1 | 3.5 GB | 90 GB | 10–19 | 37.3 GB | 56 GB |
| 2 | 2–14 | 47.4 GB | 46 GB | 20–29 | 39.1 GB | 55 GB |
| 3 | 15–39 + head | 92.5 GB | **0.9 GB**, 284 experts on the CPU | 30–39 + head | 37.3 GB | 56 GB |

| | automatic | `DS4_SPLIT=10,10,10,10` |
|---|---|---|
| Single stream, thinking on | 109.8 tok/s, cards 7 / 3 / 29 / 61 % | 111.8 tok/s, cards 26 / 22 / 22 / 28 % |
| Prefill at 64k | 2,154 tok/s | **4,079 tok/s** |
| Decode behind 64k | 107.4 tok/s, TTFT 31.4 s | 106.5 tok/s, TTFT 16.5 s |

**The single stream does not care; the prefill doubles.** A token's decode passes all 40
layers in sequence either way, but a long prompt runs the cards as a pipeline, and the
pipeline is as slow as its fullest stage. `DS4_SPLIT` is an environment variable of the
engine (`src/dsv41/ds4_model.cu`), not a flag or a config key; it is set in the server's
environment and inherited by the engine process.

## Pinned values

| Request | completion tokens on "17×23" |
|---|---|
| default | 21 (thinking in `reasoning_content`) |
| `reasoning_effort: "none"` | **2** |
| `chat_template_kwargs: {enable_thinking: false}` | **2** |
