<!-- 2026-11-08T20:53:28+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.232 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 50 | 53 | 26,895 | 505 | 0.599 s | 0.623 s | 30.0 s |
| 2 | 56 | 58 | 29,144 | 503 | 1.123 s | 1.127 s | 30.9 s |
| 8 | 61 | 58 | 29,054 | 503 | 4.502 s | 4.507 s | 33.8 s |
