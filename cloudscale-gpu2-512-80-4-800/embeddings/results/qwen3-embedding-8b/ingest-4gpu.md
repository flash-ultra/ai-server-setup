<!-- 2026-11-08T18:32:10+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.232 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 119 | 125 | 62,828 | 504 | 1.018 s | 1.058 s | 30.5 s |
| 8 | 125 | 128 | 64,385 | 504 | 1.973 s | 2.144 s | 31.3 s |
| 16 | 135 | 129 | 65,273 | 504 | 3.963 s | 4.134 s | 33.4 s |
| 32 | 152 | 130 | 65,009 | 501 | 7.828 s | 8.030 s | 37.5 s |
| 64 | 182 | 130 | 65,269 | 503 | 15.365 s | 16.110 s | 44.8 s |
| 128 | 246 | 129 | 64,692 | 502 | 30.359 s | 31.766 s | 61.1 s |
