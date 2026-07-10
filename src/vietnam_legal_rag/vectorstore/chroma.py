"""ChromaDB-backed vector store.

Provides upsert + query operations over a persistent ChromaDB collection.
Metadata filtering (``where`` clauses) is supported for domain-scoped retrieval.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import chromadb

from vietnam_legal_rag.config import get_settings

logger = logging.getLogger(__name__)


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
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    def _connect(self) -> None:
        """Lazily create the PersistentClient and get/create the collection."""
        if self._collection is not None:
            return

        persist_path = Path(self.persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        logger.info("Connecting to ChromaDB at %s", persist_path)
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Collection '%s': %d vectors",
            self.collection_name,
            self._collection.count(),
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors into the collection.

        Parameters
        ----------
        ids:
            Unique IDs for each vector (use ``chunk_id`` from metadata).
        embeddings:
            Pre-computed embedding vectors.
        documents:
            The original text content of each chunk.
        metadatas:
            Metadata dicts (must contain only str/int/float/bool values
            for ChromaDB compatibility).
        """
        self._connect()

        # ChromaDB requires metadata values to be str/int/float/bool
        clean_metadatas = [self._sanitize_metadata(m) for m in metadatas]

        # Upsert in batches to avoid memory issues with large datasets
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self._collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=clean_metadatas[i:end],
            )
        logger.info("Upserted %d vectors into '%s'", len(ids), self.collection_name)

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the top-k nearest neighbours with metadata + document text.

        Parameters
        ----------
        query_embedding:
            The query vector.
        top_k:
            Number of results to return.
        where:
            Optional ChromaDB where filter (e.g. ``{"domain": "giao_thong"}``).

        Returns
        -------
        list[dict[str, Any]]
            Each dict has keys: ``id``, ``document``, ``metadata``, ``distance``.
        """
        self._connect()

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        # Flatten from batch format to list of dicts
        hits: list[dict[str, Any]] = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                hits.append(
                    {
                        "id": doc_id,
                        "document": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )

        return hits

    def count(self) -> int:
        """Return the number of vectors in the collection."""
        self._connect()
        return self._collection.count()

    def reset(self) -> None:
        """Drop the collection and recreate it."""
        self._connect()
        logger.warning("Resetting collection '%s'", self.collection_name)
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def path(self) -> Path:
        return Path(self.persist_dir)

    @staticmethod
    def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
        """Ensure all metadata values are ChromaDB-compatible types."""
        clean = {}
        for k, v in meta.items():
            if v is None:
                clean[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        return clean


__all__ = ["VectorStore"]
