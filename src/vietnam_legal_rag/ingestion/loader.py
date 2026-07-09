"""Document loader: read raw scraped files into LangChain ``Document`` objects.

Each raw file is a pair of (``.txt``, optional ``.meta.json``) sitting under
``data/raw/<domain>/``. The loader returns a single ``Document`` per file
whose metadata carries everything downstream stages need for correct
citations (document_number, document_title, domain, source_url, …).

If the sidecar ``.meta.json`` is missing — typical for files dropped in by
hand — the loader falls back to heuristics: the first path component
becomes ``domain``, and the file stem (with ``_`` → ``/``) becomes the
best-effort ``document_number``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from langchain_core.documents import Document

# Metadata keys supplied by the loader itself; useful as a single import.
LOADER_METADATA_KEYS: tuple[str, ...] = (
    "document_number",
    "document_title",
    "domain",
    "source_url",
)


class DocumentLoader(ABC):
    """Load raw documents from disk."""

    @abstractmethod
    def load(self, source: Path) -> list[Document]:
        """Load a single file (or a directory) into a list of ``Document``s."""


class TxtDocumentLoader(DocumentLoader):
    """Load plain-text legal documents with one ``Document`` per file.

    The loader accepts either a directory (recursively) or a single ``.txt``
    file. For each file it looks for a sidecar ``<stem>.meta.json`` and
    parses it; missing or invalid sidecars are tolerated.

    The returned list contains exactly one ``Document`` per ``.txt`` file:
    one document per law, which the chunker is then responsible for splitting
    into retrieval-sized chunks.
    """

    def __init__(self, default_domain: str = "unknown") -> None:
        self.default_domain = default_domain

    # ── Public API ─────────────────────────────────────────────────────────

    def load(self, source: Path) -> list[Document]:
        """Load every ``.txt`` file in ``source`` (file or directory)."""
        if not source.exists():
            return []
        files = [source] if source.is_file() else sorted(source.glob("**/*.txt"))
        return [self._load_one(p) for p in files]

    # ── Internals ──────────────────────────────────────────────────────────

    def _load_one(self, txt_path: Path) -> Document:
        """Load a single ``.txt`` file and its sidecar ``.meta.json``.

        The raw sidecar uses :class:`RawDocument` field names (``title``,
        ``url``); this method maps them onto the canonical metadata keys
        consumed downstream (``document_title``, ``source_url``).
        """
        text = self._read_text(txt_path)
        raw_meta = self._read_meta(txt_path)
        # Map ``title`` → ``document_title`` and ``url`` → ``source_url``.
        meta: dict[str, str] = dict(raw_meta)
        if "title" in raw_meta and "document_title" not in raw_meta:
            meta["document_title"] = raw_meta["title"]
        if "url" in raw_meta and "source_url" not in raw_meta:
            meta["source_url"] = raw_meta["url"]
        # Document.metadata must be JSON-serializable (used downstream by
        # ChromaDB). Convert any non-string values defensively.
        for k, v in list(meta.items()):
            if not isinstance(v, (str, int, float, bool)) and v is not None:
                meta[k] = str(v)
        return Document(page_content=text, metadata=meta)

    @staticmethod
    def _read_text(txt_path: Path) -> str:
        """Read ``txt_path`` as UTF-8, falling back to ``errors='replace'``."""
        try:
            return txt_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Some scraped files contain stray Windows-1252 fragments; we
            # keep the file rather than fail the whole pipeline.
            return txt_path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _read_meta(txt_path: Path) -> dict[str, str]:
        """Read sidecar metadata, falling back to filename-derived defaults."""
        sidecar = txt_path.with_suffix(".meta.json")
        if sidecar.is_file():
            try:
                with sidecar.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return {str(k): ("" if v is None else str(v)) for k, v in data.items()}
            except (json.JSONDecodeError, OSError):
                # Corrupt sidecar — fall through to defaults rather than crash.
                pass
        return TxtDocumentLoader._fallback_meta(txt_path)

    @staticmethod
    def _fallback_meta(txt_path: Path) -> dict[str, str]:
        """Infer minimal metadata from the file path when no sidecar exists.

        Walks up from ``txt_path`` and uses the first directory whose name
        matches a known ``DomainSpec.name`` (``giao_thong``, ``dan_su`` …).
        If none match (e.g. a file dropped directly under ``data/raw/``),
        ``domain`` falls back to ``"unknown"``.
        """
        known_domains: set[str] = set()
        try:
            from vietnam_legal_rag.domains import DOMAIN_REGISTRY

            known_domains = set(DOMAIN_REGISTRY.keys())
        except ImportError:
            pass
        domain = "unknown"
        for parent in reversed(txt_path.parents):
            if parent.name in known_domains:
                domain = parent.name
                break
        # "23_2008_QH12" → "23/2008/QH12" (best-effort)
        document_number = txt_path.stem.replace("_", "/")
        return {
            "document_number": document_number,
            # Use the canonical key directly (no ``title`` → ``document_title``
            # mapping needed because we wrote this dict ourselves).
            "document_title": "",
            "domain": domain,
            "source_url": "",
        }


__all__ = ["DocumentLoader", "LOADER_METADATA_KEYS", "TxtDocumentLoader"]
