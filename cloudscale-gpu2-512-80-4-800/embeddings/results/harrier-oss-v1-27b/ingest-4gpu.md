<!-- 2026-11-08T19:32:11+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · max-model-len 32768 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.217 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 36 | 35 | 17,508 | 501 | 3.573 s | 3.731 s | 33.0 s |
| 8 | 39 | 35 | 17,436 | 502 | 7.022 s | 7.722 s | 35.9 s |
| 16 | 48 | 36 | 18,184 | 501 | 14.019 s | 14.564 s | 42.3 s |
| 32 | 64 | 36 | 18,154 | 501 | 27.617 s | 28.690 s | 56.5 s |
| 64 | 96 | 36 | 18,146 | 501 | 44.169 s | 57.574 s | 84.8 s |
| 128 | 160 | 36 | 18,102 | 501 | 72.806 s | 113.573 s | 141.8 s |
