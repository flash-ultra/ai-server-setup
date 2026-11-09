<!-- 2026-11-08T19:25:48+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · max-model-len 32768 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.217 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 9 | 9 | 4,570 | 502 | 3.513 s | 3.634 s | 31.7 s |
| 2 | 10 | 9 | 4,677 | 503 | 6.989 s | 7.265 s | 34.4 s |
| 4 | 12 | 9 | 4,662 | 497 | 14.011 s | 14.429 s | 41.0 s |
| 8 | 16 | 9 | 4,667 | 505 | 26.238 s | 29.222 s | 55.4 s |
| 16 | 24 | 9 | 4,666 | 501 | 44.259 s | 56.084 s | 82.5 s |
| 32 | 40 | 9 | 4,665 | 499 | 70.460 s | 110.430 s | 137.0 s |
