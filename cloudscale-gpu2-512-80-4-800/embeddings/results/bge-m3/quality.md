<!-- 2026-11-08T18:00:32+00:00 · vLLM 0.33.0 --runner pooling · BAAI/bge-m3 · max-model-len 8192 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 1024 | nDCG@10 0.6438 | R@10 0.7834 | R@100 0.9037 | corpus 1,944,533 tok in 2.0 s (973,210 tok/s) | queries 7,602 tok in 0.2 s |
| germanquad | 474 docs / 2,204 queries | dim 1024 | nDCG@10 0.9564 | R@10 0.9887 | R@100 0.9991 | corpus 218,828 tok in 0.4 s (546,485 tok/s) | queries 33,944 tok in 0.4 s |
| germandpr | 2,876 docs / 1,025 queries | dim 1024 | nDCG@10 0.8254 | R@10 0.9844 | R@100 1.0000 | corpus 898,111 tok in 1.1 s (832,446 tok/s) | queries 17,489 tok in 0.2 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 1024 | nDCG@10 0.3199 | R@10 0.4394 | R@100 0.6576 | corpus 39,273,527 tok in 53.1 s (739,726 tok/s) | queries 2,940,226 tok in 4.0 s |
