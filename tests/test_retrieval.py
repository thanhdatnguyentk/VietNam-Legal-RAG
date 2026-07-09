"""Retrieval tests — stubs to be expanded in the retrieval phase."""

from __future__ import annotations

import pytest

from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.retrieval.dense import DenseRetriever


def test_retrieval_hit_dataclass() -> None:
    hit = RetrievalHit(document=None, score=0.9, rank=1)  # type: ignore[arg-type]
    assert hit.score == 0.9
    assert hit.rank == 1


def test_dense_retriever_is_constructible() -> None:
    retriever = DenseRetriever.__new__(DenseRetriever)  # skip embedder init
    assert retriever is not None


def test_dense_retriever_retrieve_is_stub() -> None:
    class _StubEmbedder:
        pass

    class _StubStore:
        pass

    retriever = DenseRetriever(embedder=_StubEmbedder(), store=_StubStore(), top_k=3)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        retriever.retrieve("test")
