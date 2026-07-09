"""Hybrid (BM25 + dense) retriever.

SKELETON — the linear-fusion formula
``score = λ·bm25 + (1-λ)·dense`` with λ tuned on a held-out set is the
target implementation; that work belongs to a later phase.
"""

from __future__ import annotations

from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.retrieval.dense import DenseRetriever


class HybridRetriever:
    """Combine BM25 with a dense retriever."""

    def __init__(self, dense: DenseRetriever, lambda_weight: float = 0.7) -> None:
        self.dense = dense
        self.lambda_weight = lambda_weight

    def retrieve(self, query: str) -> list[RetrievalHit]:  # pragma: no cover - skeleton
        """TODO: build a BM25 index over the same corpus and fuse with dense scores."""
        raise NotImplementedError("HybridRetriever.retrieve is a skeleton.")


__all__ = ["HybridRetriever"]
