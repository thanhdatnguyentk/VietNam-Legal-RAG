"""Text chunker — split documents into retrieval-friendly pieces.

The SOTA choice for Vietnamese legal text is **structural chunking**: respect
the natural Điều / Khoản / Điểm hierarchy so that a chunk never contains a
half article. A fixed-size splitter is *not* appropriate here because it
will tear apart the rule, the exception, and the sanction clause that
typically sit within a single Khoản.

This module exposes a :class:`TextChunker` interface; the default concrete
implementation is expected to be a thin wrapper around
``langchain.text_splitter.RecursiveCharacterTextSplitter`` with
``separators=[\"\\nĐiều \", \"\\nKhoản \", \"\\nĐiểm \", \"\\n\\n\", \"\\n\", \" \"]``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.documents import Document


class TextChunker(ABC):
    """Split a list of documents into a list of smaller documents."""

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        """Return new ``Document`` objects with potentially smaller ``page_content``."""


class RecursiveVietnameseChunker(TextChunker):
    """Split using ``RecursiveCharacterTextSplitter`` tuned for Vietnamese law."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:  # pragma: no cover - skeleton
        """TODO: wire up langchain RecursiveCharacterTextSplitter with VN-aware separators."""
        raise NotImplementedError("RecursiveVietnameseChunker.split is a skeleton.")


__all__ = ["TextChunker", "RecursiveVietnameseChunker"]
