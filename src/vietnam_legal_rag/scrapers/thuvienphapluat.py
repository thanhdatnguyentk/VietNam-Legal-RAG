"""Scraper for `thuvienphapluat.vn <https://thuvienphapluat.vn>`_.

SKELETON — implementation is intentionally left for a follow-up phase.

Typical document URL shape::

    https://thuvienphapluat.vn/van-ban/Giao-thong/Luat-Giao-thong-duong-bo-2008-...

Required when implementing:

* Respect ``robots.txt`` and rate-limit requests.
* Detect and follow pagination on category pages (e.g. ``/page-2``).
* Tolerate Vietnamese diacritics (the site uses UTF-8 but occasionally
  serves CP-1252 fragments — decode defensively with ``errors="replace"``).
* Extract a stable ``document_number`` (e.g. ``100/2019/NĐ-CP``) from the
  document header when present; fall back to slug if missing.
"""

from __future__ import annotations

from pathlib import Path

from vietnam_legal_rag.scrapers.base import BaseScraper, RawDocument


class ThuvienPhapLuatScraper(BaseScraper):
    """Scraper implementation targeting thuvienphapluat.vn pages."""

    source_name = "thuvienphapluat"

    def __init__(
        self,
        base_url: str = "https://thuvienphapluat.vn",
        user_agent: str = "Mozilla/5.0 (compatible; VietnamLegalRAG/0.1)",
        timeout: int = 30,
        rate_limit_seconds: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit_seconds = rate_limit_seconds

    def fetch(self, url: str) -> str:  # pragma: no cover - skeleton
        """TODO: download HTML via ``httpx``, decode as utf-8 with ``errors="replace"``."""
        raise NotImplementedError(
            "ThuvienPhapLuatScraper.fetch is a skeleton — see module docstring."
        )

    def parse(self, raw: str, url: str) -> RawDocument:  # pragma: no cover - skeleton
        """TODO: parse the document body, title, and metadata into RawDocument."""
        raise NotImplementedError(
            "ThuvienPhapLuatScraper.parse is a skeleton — see module docstring."
        )

    def save(self, doc: RawDocument, out_dir: Path) -> Path:  # pragma: no cover - skeleton
        """TODO: write ``doc.body_text`` and a sidecar ``.meta.json`` to ``out_dir``."""
        raise NotImplementedError(
            "ThuvienPhapLuatScraper.save is a skeleton — see module docstring."
        )


__all__ = ["ThuvienPhapLuatScraper"]
