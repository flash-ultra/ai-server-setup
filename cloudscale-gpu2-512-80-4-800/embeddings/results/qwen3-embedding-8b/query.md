<!-- 2026-11-08T18:36:09+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.232 -->

### Single query, one at a time (200 queries, mean 30 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 14.9 ms | 15.1 ms | 17.5 ms | 14.9 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 1 | 68 | 14.8 ms | 15.0 ms |
| 16 | 641 | 24.6 ms | 26.9 ms |
| 64 | 1,142 | 55.4 ms | 70.6 ms |
| 256 | 1,086 | 223.5 ms | 268.5 ms |
