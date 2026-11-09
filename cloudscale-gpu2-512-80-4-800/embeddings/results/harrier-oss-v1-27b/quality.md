<!-- 2026-11-08T18:42:36+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · max-model-len 32768 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 5376 | nDCG@10 0.8001 | R@10 0.9406 | R@100 0.9833 | corpus 1,607,563 tok in 142.0 s (11,321 tok/s) | queries 11,359 tok in 0.7 s |
| germanquad | 474 docs / 2,204 queries | dim 5376 | nDCG@10 0.9770 | R@10 0.9986 | R@100 1.0000 | corpus 230,563 tok in 14.0 s (16,478 tok/s) | queries 60,492 tok in 3.9 s |
| germandpr | 2,876 docs / 1,025 queries | dim 5376 | nDCG@10 0.8086 | R@10 0.9863 | R@100 1.0000 | corpus 929,134 tok in 52.0 s (17,876 tok/s) | queries 29,502 tok in 2.2 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 5376 | nDCG@10 0.4706 | R@10 0.6102 | R@100 0.7787 | corpus 39,605,430 tok in 2202.1 s (17,985 tok/s) | queries 3,083,598 tok in 169.0 s |
