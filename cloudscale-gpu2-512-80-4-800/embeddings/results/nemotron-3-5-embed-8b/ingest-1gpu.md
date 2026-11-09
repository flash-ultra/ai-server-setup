<!-- 2026-11-08T20:01:31+00:00 · vLLM 0.33.0 --runner pooling · nvidia/Nemotron-3.5-Embed-8B-BF16 · max-model-len 32768 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.218 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 28 | 29 | 14,615 | 500 | 1.090 s | 1.133 s | 30.7 s |
| 2 | 30 | 30 | 15,220 | 503 | 2.116 s | 2.158 s | 31.8 s |
| 4 | 33 | 32 | 15,764 | 500 | 4.053 s | 4.985 s | 33.5 s |
| 8 | 36 | 31 | 15,767 | 501 | 8.213 s | 8.370 s | 36.6 s |
| 16 | 44 | 31 | 15,755 | 500 | 16.432 s | 16.468 s | 44.7 s |
| 32 | 60 | 31 | 15,731 | 501 | 31.512 s | 32.819 s | 61.1 s |
