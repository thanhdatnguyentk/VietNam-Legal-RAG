"""Scraper tests."""

from __future__ import annotations

from pathlib import Path

from vietnam_legal_rag.scrapers.base import BaseScraper, RawDocument
from vietnam_legal_rag.scrapers.thuvienphapluat import ThuvienPhapLuatScraper


def test_thuvienphapluat_scraper_is_a_base_scraper() -> None:
    scraper = ThuvienPhapLuatScraper()
    assert isinstance(scraper, BaseScraper)
    assert scraper.source_name == "thuvienphapluat"


def test_scraper_parse_extracts_title() -> None:
    """Test that parse() extracts title and body from HTML."""
    scraper = ThuvienPhapLuatScraper()
    html = """
    <html><body>
        <h1>Nghị định 100/2019/NĐ-CP về xử phạt giao thông</h1>
        <div class="content1">
            Điều 1. Phạm vi điều chỉnh
            1. Nghị định này quy định về xử phạt vi phạm hành chính.
        </div>
    </body></html>
    """
    doc = scraper.parse(html, url="https://thuvienphapluat.vn/test")
    assert isinstance(doc, RawDocument)
    assert "100/2019/NĐ-CP" in doc.title
    assert doc.document_number == "100/2019/NĐ-CP"
    assert "Điều 1" in doc.body_text


def test_scraper_save_creates_files(tmp_path: Path) -> None:
    """Test that save() creates .txt and .meta.json files."""
    scraper = ThuvienPhapLuatScraper()
    doc = RawDocument(
        url="https://example.com/test",
        title="Luật Test",
        document_number="01/2024/QH15",
        body_text="Điều 1. Nội dung test.",
        domain="giao_thong",
    )
    result = scraper.save(doc, tmp_path)
    assert result.exists()
    assert result.suffix == ".txt"
    assert result.with_suffix(".meta.json").exists()
    assert result.read_text(encoding="utf-8") == "Điều 1. Nội dung test."


def test_raw_document_suggested_filename() -> None:
    doc = RawDocument(url="", title="Test", document_number="100/2019/NĐ-CP")
    assert doc.suggested_filename() == "100_2019_NĐ-CP.txt"
