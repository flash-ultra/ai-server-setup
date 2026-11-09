<!-- 2026-11-08T18:37:33+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.232 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 1,901 | 0.122 s | 15,599 |
| 8,192 | 7,908 | 0.564 s | 14,019 |
| 32,000 | 30,771 | 3.188 s | 9,652 |
