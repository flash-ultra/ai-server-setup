<!-- 2026-11-08T20:10:56+00:00 · vLLM 0.33.0 --runner pooling · nvidia/Nemotron-3.5-Embed-8B-BF16 · max-model-len 32768 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.218 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 1,906 | 0.131 s | 14,564 |
| 8,192 | 8,001 | 0.669 s | 11,963 |
| 32,000 | 30,732 | 4.014 s | 7,657 |
