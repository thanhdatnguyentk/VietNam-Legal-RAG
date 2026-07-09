"""Dense retriever — wraps the vector store with embedding-side glue."""

from __future__ import annotations

from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.vectorstore.chroma import VectorStore


class DenseRetriever:
    """Embed the query, hit the vector store, return hits."""

    def __init__(
        self,
        embedder: VietnameseEmbedder,
        store: VectorStore,
        top_k: int = 5,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.top_k = top_k

    def retrieve(self, query: str) -> list[RetrievalHit]:  # pragma: no cover - skeleton
        """Embed ``query`` and return ranked hits."""
        raise NotImplementedError("DenseRetriever.retrieve is a skeleton.")


__all__ = ["DenseRetriever"]
