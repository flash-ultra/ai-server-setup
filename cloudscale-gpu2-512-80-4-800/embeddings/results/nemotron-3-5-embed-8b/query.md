<!-- 2026-11-08T20:09:32+00:00 · vLLM 0.33.0 --runner pooling · nvidia/Nemotron-3.5-Embed-8B-BF16 · max-model-len 32768 · queries: sequential on one copy, load on four copies -->

<!-- urls=4 model=cyberlink scenario=query tok/char=0.218 -->

### Single query, one at a time (200 queries, mean 16 tokens incl. instruction)

| p50 | p95 | p99 | mean |
|---:|---:|---:|---:|
| 15.6 ms | 16.6 ms | 18.6 ms | 15.9 ms |

### Queries under load (one query per request)

| Clients | Queries/s | p50 | p95 |
|---:|---:|---:|---:|
| 1 | 62 | 15.9 ms | 16.6 ms |
| 16 | 556 | 27.1 ms | 38.5 ms |
| 64 | 639 | 99.5 ms | 116.8 ms |
| 256 | 589 | 406.6 ms | 469.0 ms |
