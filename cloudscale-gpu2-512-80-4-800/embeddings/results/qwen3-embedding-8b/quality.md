<!-- 2026-11-08T18:13:16+00:00 · vLLM 0.33.0 --runner pooling · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 4096 | nDCG@10 0.7841 | R@10 0.9206 | R@100 0.9733 | corpus 1,707,025 tok in 27.1 s (62,915 tok/s) | queries 11,864 tok in 0.3 s |
| germanquad | 474 docs / 2,204 queries | dim 4096 | nDCG@10 0.9262 | R@10 0.9841 | R@100 0.9991 | corpus 269,172 tok in 4.9 s (55,278 tok/s) | queries 73,345 tok in 1.4 s |
| germandpr | 2,876 docs / 1,025 queries | dim 4096 | nDCG@10 0.7492 | R@10 0.9561 | R@100 0.9971 | corpus 1,090,728 tok in 17.7 s (61,572 tok/s) | queries 35,966 tok in 0.7 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 4096 | nDCG@10 0.4639 | R@10 0.6034 | R@100 0.7782 | corpus 45,416,790 tok in 783.1 s (57,998 tok/s) | queries 3,866,842 tok in 57.1 s |
