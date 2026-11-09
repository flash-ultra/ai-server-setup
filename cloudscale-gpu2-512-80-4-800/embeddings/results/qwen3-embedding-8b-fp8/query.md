<!-- 2026-11-08T20:56:09+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.232 -->

### Single query, one at a time (200 queries, mean 30 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 10.3 ms | 10.7 ms | 11.5 ms | 10.4 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 16 | 957 | 15.8 ms | 22.7 ms |
| 64 | 1,189 | 53.5 ms | 63.9 ms |
