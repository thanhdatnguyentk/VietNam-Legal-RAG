"""ChromaDB-backed vector store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vietnam_legal_rag.config import get_settings


class VectorStore:
    """Minimal wrapper around a persistent ChromaDB collection."""

    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self._client = None
        self._collection = None

    def _connect(self) -> None:  # pragma: no cover - skeleton
        """TODO: instantiate ``chromadb.PersistentClient`` and fetch the collection."""
        raise NotImplementedError("VectorStore._connect is a skeleton.")

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:  # pragma: no cover
        """Upsert vectors into the collection."""
        raise NotImplementedError("VectorStore.add is a skeleton.")

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:  # pragma: no cover
        """Return the top-k nearest neighbours with metadata + document text."""
        raise NotImplementedError("VectorStore.query is a skeleton.")

    @property
    def path(self) -> Path:
        return Path(self.persist_dir)


__all__ = ["VectorStore"]
