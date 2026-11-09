<!-- 2026-11-08T21:29:28+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · microsoft/harrier-oss-v1-27b · max-model-len 32768 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.217 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 15 | 15 | 7,608 | 502 | 2.099 s | 2.216 s | 31.7 s |
| 2 | 16 | 16 | 7,837 | 500 | 4.170 s | 4.416 s | 32.6 s |
| 8 | 22 | 15 | 7,809 | 504 | 16.734 s | 16.747 s | 45.5 s |
