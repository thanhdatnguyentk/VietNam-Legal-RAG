"""Scraper tests — stubs to be expanded in the scraping phase."""

from __future__ import annotations

import pytest

from vietnam_legal_rag.scrapers.base import BaseScraper
from vietnam_legal_rag.scrapers.thuvienphapluat import ThuvienPhapLuatScraper


def test_thuvienphapluat_scraper_is_a_base_scraper() -> None:
    scraper = ThuvienPhapLuatScraper()
    assert isinstance(scraper, BaseScraper)
    assert scraper.source_name == "thuvienphapluat"


def test_scrapers_raise_on_unimplemented_methods() -> None:
    scraper = ThuvienPhapLuatScraper()
    with pytest.raises(NotImplementedError):
        scraper.fetch("https://thuvienphapluat.vn/example")
    with pytest.raises(NotImplementedError):
        scraper.parse("<html></html>", url="https://thuvienphapluat.vn/example")
