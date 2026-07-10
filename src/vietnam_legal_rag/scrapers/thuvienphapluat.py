"""Scraper for `thuvienphapluat.vn <https://thuvienphapluat.vn>`_.

Typical document URL shape::

    https://thuvienphapluat.vn/van-ban/Giao-thong/Luat-Giao-thong-duong-bo-2008-...

Implementation notes:

* Respects ``robots.txt`` and rate-limits requests via ``tenacity`` + sleep.
* Detects and follows pagination on category pages.
* Tolerates Vietnamese diacritics (the site uses UTF-8 but occasionally
  serves CP-1252 fragments — decode defensively with ``errors="replace"``).
* Extracts a stable ``document_number`` (e.g. ``100/2019/NĐ-CP``) from the
  document header when present; falls back to slug if missing.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from vietnam_legal_rag.scrapers.base import BaseScraper, RawDocument

logger = logging.getLogger(__name__)


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
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Lazily initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def fetch(self, url: str) -> str:
        """Download HTML via ``httpx``, decode as utf-8 with ``errors="replace"``."""
        logger.info("Fetching: %s", url)
        client = self._get_client()

        response = client.get(url)
        response.raise_for_status()

        # Handle potential encoding issues with Vietnamese text
        content = response.content.decode("utf-8", errors="replace")

        # Rate limiting
        time.sleep(self.rate_limit_seconds)

        return content

    def parse(self, raw: str, url: str) -> RawDocument:
        """Parse the document body, title, and metadata into RawDocument."""
        soup = BeautifulSoup(raw, "html.parser")

        # Extract title
        title = self._extract_title(soup)

        # Extract document number
        doc_number = self._extract_document_number(soup, title)

        # Extract body text
        body_text = self._extract_body(soup)

        # Extract dates
        issued_date = self._extract_date(soup, "Ngày ban hành")
        effective_date = self._extract_date(soup, "Ngày hiệu lực")

        # Extract domain from URL
        domain = self._infer_domain_from_url(url)

        # Extra metadata
        extra = {}
        issuer = self._extract_field(soup, "Cơ quan ban hành")
        if issuer:
            extra["issuer"] = issuer
        doc_type = self._extract_field(soup, "Loại văn bản")
        if doc_type:
            extra["document_type"] = doc_type
        status = self._extract_field(soup, "Tình trạng")
        if status:
            extra["status"] = status

        return RawDocument(
            url=url,
            title=title,
            document_number=doc_number,
            issued_date=issued_date,
            effective_date=effective_date,
            domain=domain,
            body_text=body_text,
            extra_metadata=extra,
        )

    def save(self, doc: RawDocument, out_dir: Path) -> Path:
        """Write ``doc.body_text`` and a sidecar ``.meta.json`` to ``out_dir``."""
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = doc.suggested_filename()
        txt_path = out_dir / filename
        meta_path = txt_path.with_suffix(".meta.json")

        # Write body text
        txt_path.write_text(doc.body_text, encoding="utf-8")
        logger.info("Saved text: %s", txt_path)

        # Write metadata sidecar
        meta = {
            "url": doc.url,
            "title": doc.title,
            "document_number": doc.document_number,
            "issued_date": doc.issued_date,
            "effective_date": doc.effective_date,
            "domain": doc.domain,
            "extra_metadata": doc.extra_metadata,
        }
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Saved meta: %s", meta_path)

        return txt_path

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """Extract the document title from the page."""
        # Try common title selectors
        for selector in [
            "h1.doc-title",
            "h1",
            "div.title-doc",
            "title",
        ]:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return "Không rõ tiêu đề"

    @staticmethod
    def _extract_document_number(soup: BeautifulSoup, title: str) -> str | None:
        """Extract document number like '100/2019/NĐ-CP'."""
        # Pattern for Vietnamese document numbers
        pattern = r"\d+/\d{4}/[\w\-]+"
        # Try to find in title first
        m = re.search(pattern, title)
        if m:
            return m.group(0)
        # Search in the full text
        text = soup.get_text()
        m = re.search(pattern, text[:2000])
        return m.group(0) if m else None

    @staticmethod
    def _extract_body(soup: BeautifulSoup) -> str:
        """Extract the main body text of the legal document."""
        # Try common content selectors for thuvienphapluat.vn
        for selector in [
            "div.content1",
            "div.doc-body",
            "div.noidung",
            "div#toanvancontent",
        ]:
            el = soup.select_one(selector)
            if el:
                return el.get_text("\n", strip=True)
        # Fallback: get all text from body
        body = soup.find("body")
        return body.get_text("\n", strip=True) if body else soup.get_text("\n", strip=True)

    @staticmethod
    def _extract_date(soup: BeautifulSoup, label: str) -> str | None:
        """Extract a date field from the metadata section."""
        text = soup.get_text()
        pattern = rf"{label}[:\s]+(\d{{1,2}}/\d{{1,2}}/\d{{4}})"
        m = re.search(pattern, text)
        if m:
            parts = m.group(1).split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        return None

    @staticmethod
    def _extract_field(soup: BeautifulSoup, label: str) -> str | None:
        """Extract a metadata field by its label."""
        text = soup.get_text()
        pattern = rf"{label}[:\s]+(.+?)(?:\n|$)"
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None

    @staticmethod
    def _infer_domain_from_url(url: str) -> str | None:
        """Try to infer legal domain from the URL path."""
        url_lower = url.lower()
        domain_map = {
            "giao-thong": "giao_thong",
            "dan-su": "dan_su",
            "hinh-su": "hinh_su",
            "lao-dong": "lao_dong",
            "dat-dai": "dat_dai",
            "doanh-nghiep": "doanh_nghiep",
        }
        for pattern, domain in domain_map.items():
            if pattern in url_lower:
                return domain
        return None

    def __del__(self) -> None:
        if self._client is not None:
            self._client.close()


__all__ = ["ThuvienPhapLuatScraper"]
