<!-- 2026-11-08T21:31:18+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · microsoft/harrier-oss-v1-27b · max-model-len 32768 · ingest, four copies (GPU 0-3) -->

<!-- urls=4 model=cyberlink scenario=ingest tok/char=0.217 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 63 | 61 | 30,470 | 502 | 4.194 s | 4.517 s | 33.2 s |
| 32 | 87 | 60 | 29,873 | 501 | 16.115 s | 17.412 s | 46.7 s |
