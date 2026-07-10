"""Vietnamese sentence-transformer wrapper.

The wrapper exposes a small ``embed_documents`` / ``embed_query`` API so
the rest of the pipeline does not need to know which library is in use.

Supported models (via SentenceTransformer):
  - ``BAAI/bge-m3``             — SOTA multilingual, 1024-dim
  - ``keepitreal/vietnamese-sbert`` — Vietnamese-specific, 768-dim
  - ``intfloat/multilingual-e5-large`` — Alternative multilingual
"""

from __future__ import annotations

import logging
from typing import Sequence

from vietnam_legal_rag.config import get_settings

logger = logging.getLogger(__name__)


class VietnameseEmbedder:
    """Thin adapter over ``sentence_transformers.SentenceTransformer``.

    Lazy-loads the model on first use to keep imports fast.
    Supports GPU acceleration via the ``device`` parameter.
    """

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.batch_size = settings.embedding_batch_size
        self._model = None  # lazy-load on first use

    def _load(self) -> None:
        """Load the SentenceTransformer model."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        logger.info(
            "Loading embedding model '%s' on device '%s'...",
            self.model_name,
            self.device,
        )
        self._model = SentenceTransformer(
            self.model_name,
            device=self.device,
            trust_remote_code=True,
        )
        # Limit sequence length to avoid massive attention matrices and OOMs
        # (Our chunks are ~512 chars, well within 1024 tokens)
        self._model.max_seq_length = 1024
        dim = self._model.get_sentence_embedding_dimension()
        logger.info("Model loaded: %s (dim=%d)", self.model_name, dim)

    @property
    def dimension(self) -> int:
        """Return the embedding dimensionality."""
        self._load()
        return self._model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of document chunks.

        Parameters
        ----------
        texts:
            List of text chunks to embed.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.
        """
        self._load()
        embeddings = self._model.encode(
            list(texts),
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,  # for cosine similarity
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single user query.

        Parameters
        ----------
        text:
            The search query string.

        Returns
        -------
        list[float]
            A single embedding vector.
        """
        self._load()
        embedding = self._model.encode(
            text,
            normalize_embeddings=True,
        )
        return embedding.tolist()


__all__ = ["VietnameseEmbedder"]
