"""Dense retriever — wraps the vector store with embedding-side glue.

Supports:
  - Dense-only retrieval (embed query → vector search)
  - Domain-scoped filtering (restrict to specific legal domain)
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document

from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.base import RetrievalHit
from vietnam_legal_rag.vectorstore.chroma import VectorStore

logger = logging.getLogger(__name__)


class DenseRetriever:
    """Embed the query, hit the vector store, return ranked hits."""

    def __init__(
        self,
        embedder: VietnameseEmbedder,
        store: VectorStore,
        top_k: int = 5,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        domain: str | None = None,
    ) -> list[RetrievalHit]:
        """Embed ``query`` and return ranked hits.

        Parameters
        ----------
        query:
            Natural language query (e.g. "mức phạt vượt đèn đỏ").
        top_k:
            Override default number of results.
        domain:
            Optional domain filter (e.g. "giao_thong").

        Returns
        -------
        list[RetrievalHit]
            Ranked list of retrieval results with scores.
        """
        k = top_k or self.top_k

        # Embed query
        query_embedding = self.embedder.embed_query(query)

        # Build where filter for domain scoping
        where: dict[str, Any] | None = None
        if domain:
            where = {"domain": domain}

        # Query vector store
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                results = self.store.query(
                    query_embedding=query_embedding,
                    top_k=k,
                    where=where,
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.5)

        # Convert to RetrievalHit objects
        hits = []
        for rank, result in enumerate(results, start=1):
            doc = Document(
                page_content=result["document"],
                metadata=result["metadata"],
            )
            # ChromaDB returns cosine distance; convert to similarity score
            # cosine_distance = 1 - cosine_similarity → similarity = 1 - distance
            similarity = 1.0 - result.get("distance", 0.0)
            hits.append(RetrievalHit(document=doc, score=similarity, rank=rank))

        logger.info(
            "Dense retrieval: query='%s' → %d hits (top score: %.3f)",
            query[:50],
            len(hits),
            hits[0].score if hits else 0.0,
        )
        return hits


__all__ = ["DenseRetriever"]
