"""Base classes and data types for document scrapers.

The :class:`BaseScraper` defines a minimal contract:

    fetch(url)  -> raw HTML / text
    parse(raw)  -> a structured :class:`RawDocument`
    save(doc)   -> write the document to ``data/raw/`` and return its path

Subclasses are expected to handle retries, polite rate limiting, and
encoding normalization (Vietnamese legal texts frequently mix windows-1252
and utf-8 fragments).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class RawDocument:
    """A legal document as fetched from the source, before chunking."""

    url: str
    title: str
    document_number: str | None = None      # e.g. "100/2019/NĐ-CP"
    issued_date: str | None = None          # ISO 8601 if known
    effective_date: str | None = None
    domain: str | None = None               # matches a DomainSpec.name
    body_text: str = ""
    extra_metadata: dict[str, str] = field(default_factory=dict)

    def suggested_filename(self) -> str:
        """Return a stable, filesystem-safe filename for ``self``."""
        if self.document_number:
            stem = self.document_number.replace("/", "_").replace(" ", "_")
        else:
            stem = (self.title or "unknown")[:60].strip().replace(" ", "_")
            stem = "".join(c for c in stem if c.isalnum() or c in ("_", "-")) or "doc"
        return f"{stem}.txt"


class BaseScraper(ABC):
    """Abstract base class for source-specific scrapers."""

    source_name: str = "base"

    @abstractmethod
    def fetch(self, url: str) -> str:
        """Download the raw HTML/text for ``url`` and return it as a string."""

    @abstractmethod
    def parse(self, raw: str, url: str) -> RawDocument:
        """Parse raw HTML/text fetched from ``url`` into a :class:`RawDocument`."""

    @abstractmethod
    def save(self, doc: RawDocument, out_dir: Path) -> Path:
        """Persist ``doc`` to ``out_dir``; return the written file path."""

    def run(self, urls: Iterable[str], out_dir: Path) -> list[Path]:
        """Drive the full fetch-parse-save loop over ``urls``."""
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for url in urls:
            raw = self.fetch(url)
            doc = self.parse(raw, url=url)
            written.append(self.save(doc, out_dir))
        return written


__all__ = ["BaseScraper", "RawDocument"]
