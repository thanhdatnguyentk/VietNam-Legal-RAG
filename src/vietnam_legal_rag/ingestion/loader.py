"""Document loader: read raw scraped files into LangChain ``Document`` objects.

The loader is intentionally minimal — its only job is to read files and
attach metadata. Chunking happens in :mod:`vietnam_legal_rag.ingestion.chunker`.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


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

    def load(self, source: Path) -> list[Document]:
        """Read ``.txt`` + ``.meta.json`` pairs and yield Document instances.

        Parameters
        ----------
        source:
            Either a single ``.txt`` file or a directory.  When a directory is
            given, every ``.txt`` inside it (recursively) is loaded.

        Returns
        -------
        list[Document]
            One ``Document`` per file, with metadata from the sidecar JSON.
        """
        if source.is_dir():
            return self._load_directory(source)
        return self._load_file(source)

    def _load_directory(self, directory: Path) -> list[Document]:
        """Load all ``.txt`` files in a directory tree."""
        documents: list[Document] = []
        for txt_file in sorted(directory.rglob("*.txt")):
            if txt_file.name == ".gitkeep":
                continue
            documents.extend(self._load_file(txt_file))
        return documents

    def _load_file(self, txt_file: Path) -> list[Document]:
        """Load a single ``.txt`` file and its sidecar ``.meta.json``."""
        if not txt_file.exists():
            logger.warning("File not found: %s", txt_file)
            return []

        # Read body text
        body = txt_file.read_text(encoding="utf-8")
        if not body.strip():
            logger.warning("Empty file: %s", txt_file)
            return []

        # Read sidecar metadata
        meta_path = txt_file.with_suffix(".meta.json")
        metadata = self._read_sidecar(meta_path)

        # Ensure essential fields
        metadata.setdefault("source_file", str(txt_file))
        metadata.setdefault("domain", txt_file.parent.name)

        # Flatten extra_metadata into the top level
        extra = metadata.pop("extra_metadata", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                metadata.setdefault(k, v)

        return [Document(page_content=body, metadata=metadata)]

    @staticmethod
    def _read_sidecar(meta_path: Path) -> dict:
        """Read the ``.meta.json`` sidecar file if it exists."""
        if not meta_path.exists():
            logger.debug("No sidecar metadata: %s", meta_path)
            return {}
        try:
            raw = meta_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                logger.warning("Sidecar is not a JSON object: %s", meta_path)
                return {}
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read sidecar %s: %s", meta_path, exc)
            return {}


__all__ = ["DocumentLoader", "TxtDocumentLoader"]
