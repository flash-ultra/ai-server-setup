<!-- 2026-11-08T20:44:10+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · Qwen/Qwen3-Embedding-8B · max-model-len 32768 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 4096 | nDCG@10 0.7800 | R@10 0.9217 | R@100 0.9767 | corpus 1,707,025 tok in 15.8 s (108,150 tok/s) | queries 11,864 tok in 0.3 s |
| germanquad | 474 docs / 2,204 queries | dim 4096 | nDCG@10 0.9708 | R@10 0.9964 | R@100 1.0000 | corpus 269,172 tok in 2.8 s (94,581 tok/s) | queries 64,529 tok in 1.3 s |
| germandpr | 2,876 docs / 1,025 queries | dim 4096 | nDCG@10 0.8426 | R@10 0.9912 | R@100 0.9990 | corpus 1,090,728 tok in 10.3 s (105,756 tok/s) | queries 31,866 tok in 0.7 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 4096 | nDCG@10 0.4493 | R@10 0.5849 | R@100 0.7660 | corpus 45,416,790 tok in 487.5 s (93,160 tok/s) | queries 3,744,502 tok in 34.5 s |
