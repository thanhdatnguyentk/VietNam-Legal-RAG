"""Cross-Encoder Reranker — Stage 2 of the two-stage retrieval pipeline.

Uses a cross-encoder model (e.g. ``bge-reranker-v2-m3``) to re-score
candidate documents against the query. Unlike bi-encoder (embedding) models
that encode query and document independently, a cross-encoder processes them
*jointly*, enabling much more accurate relevance judgements at the cost of
higher latency.

Usage::

    reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3")
    reranked_hits = reranker.rerank(query, candidate_hits, top_k=5)
"""

from __future__ import annotations

import logging
from typing import Sequence

from vietnam_legal_rag.retrieval.base import RetrievalHit

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Rerank retrieval hits using a cross-encoder model.

    Parameters
    ----------
    model_name:
        HuggingFace model ID for the cross-encoder. Default is
        ``BAAI/bge-reranker-v2-m3`` which supports multilingual input
        including Vietnamese.
    device:
        Torch device string (``cuda``, ``cpu``, ``mps``).
    batch_size:
        Number of query-document pairs to score in a single batch.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str | None = None,
        batch_size: int = 8,
        max_length: int = 512,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self._model = None
        self._device = device

    def _lazy_load(self) -> None:
        """Load the cross-encoder model on first use."""
        if self._model is not None:
            return

        from sentence_transformers import CrossEncoder
        import torch

        device = self._device
        if device is None:
            if torch.cuda.is_available():
                # Check if there is enough GPU memory (need ~2GB for reranker)
                free_mem = torch.cuda.mem_get_info()[0] / (1024**3)
                device = "cuda" if free_mem > 2.0 else "cpu"
                if device == "cpu":
                    logger.warning(
                        "Only %.1f GB GPU memory free, loading reranker on CPU", free_mem
                    )
            else:
                device = "cpu"

        logger.info("Loading CrossEncoder model: %s on %s", self.model_name, device)
        self._model = CrossEncoder(self.model_name, device=device)
        logger.info("CrossEncoder loaded successfully.")

    def rerank(
        self,
        query: str,
        hits: Sequence[RetrievalHit],
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[RetrievalHit]:
        """Re-score and re-order hits using cross-encoder.

        Parameters
        ----------
        query:
            The user's natural language query.
        hits:
            Candidate hits from Stage 1 (e.g. Hybrid Retriever).
        top_k:
            Maximum number of results to return after reranking.
        threshold:
            Optional minimum cross-encoder score. Hits below this score
            are dropped. If ``None``, returns the top_k regardless of score.

        Returns
        -------
        list[RetrievalHit]
            Reranked hits sorted by cross-encoder score descending.
        """
        if not hits:
            return []

        self._lazy_load()

        # Build (query, document) pairs — truncate to max_length to save VRAM
        pairs = [
            (query, hit.document.page_content[:self.max_length])
            for hit in hits
        ]

        # Score all pairs
        scores = self._model.predict(pairs, batch_size=self.batch_size)

        # Pair hits with new scores
        scored_hits = list(zip(hits, scores))

        # Apply threshold filter if specified
        if threshold is not None:
            scored_hits = [(h, s) for h, s in scored_hits if s >= threshold]

            # Fallback: if everything was filtered, return top-2 anyway
            if not scored_hits:
                logger.warning(
                    "All %d candidates below threshold %.3f, falling back to top-2",
                    len(hits),
                    threshold,
                )
                scored_hits = sorted(
                    zip(hits, scores), key=lambda x: x[1], reverse=True
                )[:2]

        # Sort by cross-encoder score descending
        scored_hits.sort(key=lambda x: x[1], reverse=True)

        # Build final results
        results = []
        for rank, (hit, ce_score) in enumerate(scored_hits[:top_k], start=1):
            results.append(
                RetrievalHit(
                    document=hit.document,
                    score=float(ce_score),
                    rank=rank,
                )
            )

        logger.info(
            "Reranked %d → %d hits (query='%s...')",
            len(hits),
            len(results),
            query[:40],
        )
        return results


__all__ = ["CrossEncoderReranker"]
