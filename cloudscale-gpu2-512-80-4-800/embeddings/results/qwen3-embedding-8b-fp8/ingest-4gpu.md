<!-- 2026-11-08T20:55:04+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.232 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 217 | 225 | 113,365 | 504 | 1.128 s | 1.215 s | 30.9 s |
| 32 | 241 | 225 | 112,943 | 503 | 4.504 s | 4.754 s | 34.3 s |
