"""BM25 sparse retriever + Hybrid (BM25 + Dense) two-stage retriever.

The HybridRetriever implements Reciprocal Rank Fusion (RRF) to combine
BM25 keyword matching with dense semantic search for optimal recall.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from vietnam_legal_rag.retrieval.base import RetrievalHit

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Sparse BM25 retriever over pre-loaded document chunks.

    Uses ``rank_bm25`` library for efficient BM25 scoring.
    Documents are loaded from JSONL files at init time.
    """

    def __init__(
        self,
        processed_dir: str | Path | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.processed_dir = Path(processed_dir) if processed_dir else None
        self.k1 = k1
        self.b = b
        self._documents: list[Document] = []
        self._index = None
        self._loaded = False

    def _load(self) -> None:
        """Load documents and build BM25 index."""
        if self._loaded:
            return

        from rank_bm25 import BM25Okapi

        if self.processed_dir is None:
            from vietnam_legal_rag.paths import PROCESSED_DIR
            self.processed_dir = PROCESSED_DIR

        # Load all chunks from JSONL files
        self._documents = []
        for jsonl_file in sorted(self.processed_dir.rglob("*.jsonl")):
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    doc = Document(
                        page_content=rec["text"],
                        metadata=rec.get("metadata", {}),
                    )
                    self._documents.append(doc)

        if not self._documents:
            logger.warning("BM25: no documents found in %s", self.processed_dir)
            self._loaded = True
            return

        # Tokenize (simple whitespace + lowering for Vietnamese)
        tokenized = [self._tokenize(doc.page_content) for doc in self._documents]
        self._index = BM25Okapi(tokenized, k1=self.k1, b=self.b)
        self._loaded = True
        logger.info("BM25 index built: %d documents", len(self._documents))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace tokenizer for Vietnamese text."""
        return text.lower().split()

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        domain: str | None = None,
    ) -> list[RetrievalHit]:
        """Retrieve documents using BM25 scoring.

        Parameters
        ----------
        query:
            Natural language query.
        top_k:
            Number of results to return.
        domain:
            Optional domain filter applied post-retrieval.
        """
        self._load()

        if not self._documents or self._index is None:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._index.get_scores(tokenized_query)

        # Pair documents with scores and sort
        scored_docs = list(zip(self._documents, scores))

        # Apply domain filter if specified
        if domain:
            scored_docs = [
                (doc, score) for doc, score in scored_docs
                if doc.metadata.get("domain") == domain
            ]

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        hits = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], start=1):
            hits.append(RetrievalHit(document=doc, score=float(score), rank=rank))

        return hits


class HybridRetriever:
    """Two-stage hybrid retriever: BM25 + Dense with Reciprocal Rank Fusion.

    Stage 1: Retrieve candidates from both BM25 and Dense retrievers
    Stage 2: Fuse rankings using RRF for final ranking

    This approach combines:
    - BM25: Good at keyword matching (exact legal terms, document numbers)
    - Dense: Good at semantic similarity (understanding intent)
    """

    def __init__(
        self,
        dense_retriever: Any,
        bm25_retriever: BM25Retriever,
        dense_weight: float = 0.6,
        bm25_weight: float = 0.4,
        rrf_k: int = 60,
    ) -> None:
        """
        Parameters
        ----------
        dense_retriever:
            DenseRetriever instance for semantic search.
        bm25_retriever:
            BM25Retriever instance for keyword search.
        dense_weight:
            Weight for dense retrieval scores in RRF.
        bm25_weight:
            Weight for BM25 scores in RRF.
        rrf_k:
            RRF constant (default 60, as per original paper).
        """
        self.dense = dense_retriever
        self.bm25 = bm25_retriever
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        dense_candidates: int = 20,
        bm25_candidates: int = 20,
        domain: str | None = None,
    ) -> list[RetrievalHit]:
        """Retrieve using hybrid BM25 + Dense with RRF fusion.

        Parameters
        ----------
        query:
            Natural language query.
        top_k:
            Number of final results to return.
        dense_candidates:
            Number of candidates from dense retriever.
        bm25_candidates:
            Number of candidates from BM25 retriever.
        domain:
            Optional domain filter.
        """
        # Stage 1: Get candidates from both retrievers
        dense_hits = self.dense.retrieve(query, top_k=dense_candidates, domain=domain)
        bm25_hits = self.bm25.retrieve(query, top_k=bm25_candidates, domain=domain)

        # Stage 2: Reciprocal Rank Fusion
        # RRF score = Σ weight / (k + rank)
        fused_scores: dict[str, float] = {}
        hit_docs: dict[str, RetrievalHit] = {}

        # Process dense hits
        for hit in dense_hits:
            doc_id = hit.document.metadata.get("chunk_id", str(id(hit)))
            rrf_score = self.dense_weight / (self.rrf_k + hit.rank)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + rrf_score
            hit_docs[doc_id] = hit

        # Process BM25 hits
        for hit in bm25_hits:
            doc_id = hit.document.metadata.get("chunk_id", str(id(hit)))
            rrf_score = self.bm25_weight / (self.rrf_k + hit.rank)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + rrf_score
            if doc_id not in hit_docs:
                hit_docs[doc_id] = hit

        # Sort by fused RRF score
        ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        # Build final result list
        results = []
        for rank, (doc_id, score) in enumerate(ranked[:top_k], start=1):
            original_hit = hit_docs[doc_id]
            results.append(
                RetrievalHit(
                    document=original_hit.document,
                    score=score,
                    rank=rank,
                )
            )

        logger.info(
            "Hybrid retrieval: query='%s' → dense=%d, bm25=%d → fused=%d hits",
            query[:50],
            len(dense_hits),
            len(bm25_hits),
            len(results),
        )
        return results


class RerankedHybridRetriever:
    """Full two-stage retriever: Hybrid (BM25 + Dense) → Cross-Encoder Rerank.

    Stage 1: Hybrid retriever gathers a large candidate pool (e.g. top-50)
    Stage 2: Cross-Encoder reranker re-scores and selects the final top-k

    This is the recommended production configuration for legal RAG.
    """

    def __init__(
        self,
        dense_retriever: Any,
        bm25_retriever: BM25Retriever,
        reranker_model: str = "BAAI/bge-reranker-v2-m3",
        dense_weight: float = 0.5,
        bm25_weight: float = 0.5,
        stage1_candidates: int = 50,
        reranker_device: str | None = None,
    ) -> None:
        from vietnam_legal_rag.retrieval.reranker import CrossEncoderReranker

        self.hybrid = HybridRetriever(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
            dense_weight=dense_weight,
            bm25_weight=bm25_weight,
        )
        self.reranker = CrossEncoderReranker(
            model_name=reranker_model,
            device=reranker_device,
        )
        self.stage1_candidates = stage1_candidates

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
        threshold: float | None = None,
    ) -> list[RetrievalHit]:
        """Retrieve with two-stage pipeline: Hybrid → Rerank.

        Parameters
        ----------
        query:
            Natural language query.
        top_k:
            Number of final results after reranking.
        domain:
            Optional domain filter.
        threshold:
            Optional minimum cross-encoder score.
        """
        # Stage 1: Get broad candidate pool from Hybrid
        candidates = self.hybrid.retrieve(
            query,
            top_k=self.stage1_candidates,
            domain=domain,
        )

        # Stage 2: Rerank with cross-encoder
        reranked = self.reranker.rerank(
            query,
            candidates,
            top_k=top_k,
            threshold=threshold,
        )

        logger.info(
            "RerankedHybrid: %d candidates → %d reranked (query='%s...')",
            len(candidates),
            len(reranked),
            query[:40],
        )
        return reranked


__all__ = ["BM25Retriever", "HybridRetriever", "RerankedHybridRetriever"]
