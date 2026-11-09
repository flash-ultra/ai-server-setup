<!-- 2026-11-08T18:28:14+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.232 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 30 | 32 | 16,042 | 503 | 1.001 s | 1.040 s | 30.1 s |
| 2 | 32 | 33 | 16,709 | 506 | 1.958 s | 1.964 s | 31.0 s |
| 4 | 34 | 33 | 16,685 | 505 | 3.922 s | 3.928 s | 32.9 s |
| 8 | 38 | 33 | 16,658 | 504 | 7.851 s | 7.868 s | 36.8 s |
| 16 | 46 | 33 | 16,640 | 503 | 15.227 s | 15.721 s | 44.5 s |
| 32 | 62 | 33 | 16,606 | 504 | 30.356 s | 30.966 s | 60.2 s |
