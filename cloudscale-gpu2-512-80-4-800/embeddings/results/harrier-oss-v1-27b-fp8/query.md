<!-- 2026-11-08T21:32:39+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · microsoft/harrier-oss-v1-27b · max-model-len 32768 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.217 -->

### Single query, one at a time (200 queries, mean 28 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 24.9 ms | 25.5 ms | 27.5 ms | 25.0 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 16 | 344 | 45.6 ms | 52.6 ms |
| 64 | 782 | 82.0 ms | 107.4 ms |
