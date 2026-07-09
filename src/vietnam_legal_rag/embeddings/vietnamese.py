"""Vietnamese sentence-transformer wrapper.

The wrapper exposes a small ``embed_documents`` / ``embed_query`` API so
the rest of the pipeline does not need to know which library is in use.
"""

from __future__ import annotations

from vietnam_legal_rag.config import get_settings


class VietnameseEmbedder:
    """Thin adapter over ``sentence_transformers.SentenceTransformer``."""

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self._model = None  # lazy-load on first use to keep import light

    def _load(self) -> None:  # pragma: no cover - skeleton
        """TODO: ``from sentence_transformers import SentenceTransformer; …``"""
        raise NotImplementedError("VietnameseEmbedder._load is a skeleton.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        """Embed a batch of document chunks."""
        raise NotImplementedError("VietnameseEmbedder.embed_documents is a skeleton.")

    def embed_query(self, text: str) -> list[float]:  # pragma: no cover
        """Embed a single user query."""
        raise NotImplementedError("VietnameseEmbedder.embed_query is a skeleton.")


__all__ = ["VietnameseEmbedder"]
