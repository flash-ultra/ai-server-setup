<!-- 2026-11-08T19:40:17+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · max-model-len 32768 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.217 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 1,897 | 0.427 s | 4,443 |
| 8,192 | 7,994 | 1.780 s | 4,491 |
| 32,000 | 30,725 | 7.081 s | 4,339 |
