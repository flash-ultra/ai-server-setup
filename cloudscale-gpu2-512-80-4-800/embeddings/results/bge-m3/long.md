<!-- 2026-11-08T18:09:07+00:00 · vLLM 0.33.0 --runner pooling · BAAI/bge-m3 · max-model-len 8192 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.254 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 2,021 | 0.016 s | 123,254 |
| 8,000 | 7,922 | 0.064 s | 123,465 |
