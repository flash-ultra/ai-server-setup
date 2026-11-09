<!-- 2026-11-08T20:56:52+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.232 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 1,901 | 0.076 s | 25,162 |
| 8,192 | 7,908 | 0.365 s | 21,682 |
| 32,000 | 30,771 | 2.401 s | 12,818 |
