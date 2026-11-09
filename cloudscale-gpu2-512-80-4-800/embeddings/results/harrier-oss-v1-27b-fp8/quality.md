<!-- 2026-11-08T21:03:01+00:00 · vLLM 0.33.0 --runner pooling --quantization fp8 · microsoft/harrier-oss-v1-27b · max-model-len 32768 · quality, four copies, truncate 8192 -->

| Task | Size | Dim | nDCG@10 | Recall@10 | Recall@100 | Corpus | Queries |
|---|---|---|---|---|---|---|---|
| scifact | 5,183 docs / 300 queries | dim 5376 | nDCG@10 0.7970 | R@10 0.9406 | R@100 0.9833 | corpus 1,607,563 tok in 105.8 s (15,198 tok/s) | queries 11,359 tok in 0.5 s |
| germanquad | 474 docs / 2,204 queries | dim 5376 | nDCG@10 0.9778 | R@10 0.9986 | R@100 1.0000 | corpus 230,563 tok in 8.9 s (25,886 tok/s) | queries 60,492 tok in 2.7 s |
| germandpr | 2,876 docs / 1,025 queries | dim 5376 | nDCG@10 0.8103 | R@10 0.9883 | R@100 1.0000 | corpus 929,134 tok in 32.0 s (29,000 tok/s) | queries 29,502 tok in 1.5 s |
| gerdalir | 9,969 docs / 12,234 queries | dim 5376 | nDCG@10 0.4686 | R@10 0.6068 | R@100 0.7769 | corpus 39,605,430 tok in 1330.0 s (29,779 tok/s) | queries 3,083,598 tok in 99.9 s |
