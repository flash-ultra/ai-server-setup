<!-- 2026-11-08T21:33:25+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · microsoft/harrier-oss-v1-27b · max-model-len 32768 · long documents, one copy -->

<!-- urls=1 model=cyberlink scenario=long tok/char=0.217 -->

### One long document per request

| Target tokens | Tokens | Latency (median of reps) | Input tok/s |
|---:|---:|---:|---:|
| 2,048 | 1,897 | 0.257 s | 7,393 |
| 8,192 | 7,994 | 1.082 s | 7,388 |
| 32,000 | 30,725 | 4.424 s | 6,944 |
