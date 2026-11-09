<!-- 2026-11-08T19:38:46+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · max-model-len 32768 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.217 -->

### Single query, one at a time (200 queries, mean 28 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 43.9 ms | 44.6 ms | 45.5 ms | 43.6 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 1 | 23 | 43.9 ms | 44.6 ms |
| 16 | 195 | 80.6 ms | 89.2 ms |
| 64 | 583 | 108.3 ms | 137.9 ms |
| 256 | 828 | 290.7 ms | 390.6 ms |
