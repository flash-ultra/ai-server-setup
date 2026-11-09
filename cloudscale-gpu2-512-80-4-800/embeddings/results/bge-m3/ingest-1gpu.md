<!-- 2026-11-08T18:01:38+00:00 · vLLM 0.33.0 --runner pooling · BAAI/bge-m3 · max-model-len 8192 · ingest, one copy (GPU 0) -->

<!-- urls=1 model=cyberlink scenario=ingest tok/char=0.254 -->

### Ingest: 32 chunks of ~512 tokens per request

| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 301 | 321 | 160,906 | 502 | 0.099 s | 0.103 s | 30.0 s |
| 2 | 530 | 564 | 282,380 | 501 | 0.109 s | 0.135 s | 30.1 s |
| 4 | 549 | 582 | 291,754 | 501 | 0.218 s | 0.240 s | 30.2 s |
| 8 | 551 | 581 | 290,500 | 500 | 0.437 s | 0.463 s | 30.4 s |
| 16 | 558 | 579 | 289,831 | 501 | 0.876 s | 0.901 s | 30.8 s |
| 32 | 572 | 578 | 289,021 | 500 | 1.753 s | 1.785 s | 31.7 s |
