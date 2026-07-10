# Ablation Study Results (Top-5)

**Date**: 2026-07-10 | **Testset**: data/eval/questions.v2.jsonl

| Configuration | Precision | Recall |
|---|---|---|
| Dense-Only | 63.00% | 63.00% |
| BM25-Only | 70.00% | 70.00% |
| Hybrid (D=0.3, B=0.7) | 68.50% | 68.50% |
| Hybrid (D=0.5, B=0.5) | 69.50% | 69.50% |
| Hybrid (D=0.6, B=0.4) | 65.00% | 65.00% |
| Hybrid (D=0.7, B=0.3) | 65.00% | 65.00% |
| Hybrid (D=0.8, B=0.2) | 63.50% | 63.50% |
| Hybrid+Reranker (D=0.5, B=0.5, Top50→5) | 74.00% | 74.00% |
| Hybrid+Reranker (D=0.3, B=0.7, Top50→5) | 74.00% | 74.00% |

**Best**: Hybrid+Reranker (D=0.5, B=0.5, Top50→5) → Recall@5 = 74.00%
