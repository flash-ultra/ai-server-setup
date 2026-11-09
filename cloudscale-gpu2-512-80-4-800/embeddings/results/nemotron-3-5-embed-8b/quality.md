<!-- 2026-11-08T19:43:57+00:00 · vLLM 0.33.0 --runner pooling · nvidia/Nemotron-3.5-Embed-8B-BF16 · max-model-len 32768 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 4096 | nDCG@10 0.8330 | R@10 0.9467 | R@100 0.9900 | corpus 1,628,373 tok in 27.9 s (58,358 tok/s) | queries 6,059 tok in 0.5 s |
| germanquad | 474 docs / 2,204 queries | dim 4096 | nDCG@10 0.9867 | R@10 0.9995 | R@100 1.0000 | corpus 227,065 tok in 4.5 s (50,545 tok/s) | queries 34,338 tok in 2.8 s |
| germandpr | 2,876 docs / 1,025 queries | dim 4096 | nDCG@10 0.8699 | R@10 0.9971 | R@100 1.0000 | corpus 922,631 tok in 16.1 s (57,202 tok/s) | queries 17,278 tok in 1.4 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 4096 | nDCG@10 0.5474 | R@10 0.6813 | R@100 0.8159 | corpus 46,125,194 tok in 944.9 s (48,813 tok/s) | queries 2,975,123 tok in 50.2 s |
