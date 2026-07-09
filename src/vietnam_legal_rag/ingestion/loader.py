"""Document loader: read raw scraped files into LangChain ``Document`` objects.

The loader is intentionally minimal — its only job is to read files and
attach metadata. Chunking happens in :mod:`vietnam_legal_rag.ingestion.chunker`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from langchain_core.documents import Document


class DocumentLoader(ABC):
    """Load raw documents from disk."""

    @abstractmethod
    def load(self, source: Path) -> list[Document]:
        """Load a single file (or a directory) into a list of ``Document``s."""


class TxtDocumentLoader(DocumentLoader):
    """Load plain-text legal documents with one Document per file.

    Each file becomes exactly one ``Document`` whose ``page_content`` is
    the full body and whose ``metadata`` carries the document number,
    title, and source URL when available (read from a sidecar ``.meta.json``
    produced by the scraper).
    """

    def load(self, source: Path) -> list[Document]:  # pragma: no cover - skeleton
        """TODO: read .txt + .meta.json pairs and yield Document instances."""
        raise NotImplementedError("TxtDocumentLoader.load is a skeleton.")


__all__ = ["DocumentLoader", "TxtDocumentLoader"]
