<!-- 2026-11-08T18:07:45+00:00 · vLLM 0.33.0 --runner pooling · BAAI/bge-m3 · max-model-len 8192 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.254 -->

### Single query, one at a time (200 queries, mean 16 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 6.0 ms | 6.2 ms | 8.3 ms | 6.1 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 1 | 165 | 6.0 ms | 6.2 ms |
| 16 | 1,481 | 10.3 ms | 14.2 ms |
| 64 | 1,903 | 33.4 ms | 38.2 ms |
| 256 | 1,842 | 129.1 ms | 161.3 ms |
