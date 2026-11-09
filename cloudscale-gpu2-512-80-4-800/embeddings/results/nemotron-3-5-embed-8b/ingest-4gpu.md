<!-- 2026-11-08T20:05:30+00:00 · vLLM 0.33.0 --runner pooling · nvidia/Nemotron-3.5-Embed-8B-BF16 · max-model-len 32768 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.218 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 110 | 114 | 57,221 | 501 | 1.113 s | 1.156 s | 30.8 s |
| 8 | 116 | 116 | 58,054 | 501 | 2.146 s | 2.294 s | 32.0 s |
| 16 | 128 | 122 | 60,890 | 501 | 4.112 s | 4.377 s | 33.7 s |
| 32 | 144 | 124 | 61,845 | 499 | 8.226 s | 8.422 s | 37.2 s |
| 64 | 176 | 123 | 61,474 | 501 | 16.409 s | 16.756 s | 45.9 s |
| 128 | 236 | 123 | 61,314 | 500 | 31.126 s | 33.631 s | 61.6 s |
