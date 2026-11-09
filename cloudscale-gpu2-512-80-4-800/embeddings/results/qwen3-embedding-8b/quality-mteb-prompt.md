<!-- 2026-11-08T20:15:12+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · German tasks with the MTEB default prompt -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| germanquad | 474 docs / 2,204 queries | dim 4096 | nDCG@10 0.9704 | R@10 0.9964 | R@100 1.0000 | corpus 269,172 tok in 4.7 s (57,070 tok/s) | queries 64,529 tok in 1.7 s |
| germandpr | 2,876 docs / 1,025 queries | dim 4096 | nDCG@10 0.8439 | R@10 0.9912 | R@100 0.9990 | corpus 1,090,728 tok in 17.4 s (62,508 tok/s) | queries 31,866 tok in 1.0 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 4096 | nDCG@10 0.4497 | R@10 0.5849 | R@100 0.7666 | corpus 45,416,790 tok in 782.9 s (58,009 tok/s) | queries 3,744,502 tok in 57.4 s |
