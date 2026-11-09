<!-- 2026-11-08T18:04:42+00:00 · vLLM 0.33.0 --runner pooling · BAAI/bge-m3 · max-model-len 8192 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.254 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 1225 | 1,305 | 653,710 | 501 | 0.098 s | 0.101 s | 30.0 s |
| 8 | 2113 | 2,247 | 1,124,568 | 500 | 0.109 s | 0.136 s | 30.1 s |
| 16 | 2187 | 2,318 | 1,160,029 | 501 | 0.218 s | 0.235 s | 30.2 s |
| 32 | 2190 | 2,304 | 1,154,187 | 501 | 0.439 s | 0.465 s | 30.4 s |
| 64 | 2202 | 2,283 | 1,142,647 | 501 | 0.884 s | 0.916 s | 30.9 s |
| 128 | 2237 | 2,254 | 1,128,737 | 501 | 1.774 s | 1.823 s | 31.8 s |
