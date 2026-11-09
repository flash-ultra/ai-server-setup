<!-- 2026-11-08T20:33:56+00:00 · vLLM 0.33.0 --runner pooling · microsoft/harrier-oss-v1-27b · German QA tasks with our own instruction -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| germanquad | 474 docs / 2,204 queries | dim 5376 | nDCG@10 0.9784 | R@10 0.9991 | R@100 1.0000 | corpus 230,563 tok in 66.6 s (3,463 tok/s) | queries 67,104 tok in 3.0 s |
| germandpr | 2,876 docs / 1,025 queries | dim 5376 | nDCG@10 0.8481 | R@10 0.9980 | R@100 1.0000 | corpus 929,134 tok in 53.8 s (17,279 tok/s) | queries 32,577 tok in 1.6 s |
