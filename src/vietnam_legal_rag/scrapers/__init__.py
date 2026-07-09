"""Web scrapers for collecting Vietnamese legal documents.

A scraper is responsible for fetching a list of source URLs, extracting the
structured document content, and writing it to ``data/raw/``. Concrete
scrapers subclass :class:`BaseScraper`.
"""

from __future__ import annotations

from vietnam_legal_rag.scrapers.base import BaseScraper, RawDocument

__all__ = ["BaseScraper", "RawDocument"]
