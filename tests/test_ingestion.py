"""Tests for phase 2 — real loader, real chunker, real pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vietnam_legal_rag.ingestion._regex import (
    ARTICLE_PATTERN,
    CLAUSE_PATTERN,
    POINT_PATTERN,
)
from vietnam_legal_rag.ingestion.chunker import (
    RecursiveVietnameseChunker,
    parse_articles,
)
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import collect_raw_files, run_ingestion
from vietnam_legal_rag.paths import RAW_DIR

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TXT = FIXTURES_DIR / "sample_law.txt"
SAMPLE_META = FIXTURES_DIR / "sample_law.meta.json"

REQUIRED_CHUNK_KEYS = {
    "document_number",
    "document_title",
    "domain",
    "article",
    "article_title",
    "clause",
    "point",
    "chunk_id",
    "source_url",
}


# ────────────────────────────────────────────────────────────────────────────
# Regex patterns
# ────────────────────────────────────────────────────────────────────────────


def test_regex_article_pattern_matches_typical_headings() -> None:
    matches = list(ARTICLE_PATTERN.finditer("Điều 1. Phạm vi\nĐiều 23: Nội dung\nĐiều 15 Quy định"))
    articles = [m.group(1) for m in matches]
    assert articles == ["1", "23", "15"]


def test_regex_clause_pattern_matches_dot_and_paren() -> None:
    matches = list(CLAUSE_PATTERN.finditer("1. Một\n2) Hai\n3. Ba"))
    assert [m.group(1) for m in matches] == ["1", "2", "3"]


def test_regex_clause_pattern_keeps_first_letter() -> None:
    """Body re-anchor should keep "Đây" (not "ây")."""
    m = CLAUSE_PATTERN.search("1. Đây là khoản 1")
    assert m is not None
    assert m.group(2) == "Đ"


def test_regex_point_pattern_matches_vietnamese_letters() -> None:
    text = "a) Một\nb) Hai\nđ) Ba"
    matches = list(POINT_PATTERN.finditer(text))
    letters = [m.group(1) for m in matches]
    assert letters == ["a", "b", "đ"]


# ────────────────────────────────────────────────────────────────────────────
# Loader
# ────────────────────────────────────────────────────────────────────────────


def test_loader_loads_txt_with_meta(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "23_2008.txt").write_text("Nội dung luật", encoding="utf-8")
    (raw_dir / "23_2008.meta.json").write_text(
        json.dumps(
            {
                "url": "https://example/law",
                "title": "Luật test",
                "document_number": "23/2008/QH12",
                "domain": "giao_thong",
            }
        ),
        encoding="utf-8",
    )
    loader = TxtDocumentLoader()
    docs = loader.load(raw_dir)
    assert len(docs) == 1
    assert docs[0].page_content == "Nội dung luật"
    assert docs[0].metadata["document_number"] == "23/2008/QH12"
    assert docs[0].metadata["domain"] == "giao_thong"
    assert docs[0].metadata["url"] == "https://example/law"


def test_loader_handles_missing_meta_via_filename(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    (raw_dir / "giao_thong").mkdir(parents=True)
    (raw_dir / "giao_thong" / "23_2008_QH12.txt").write_text("body", encoding="utf-8")
    loader = TxtDocumentLoader()
    docs = loader.load(raw_dir)
    assert len(docs) == 1
    assert docs[0].metadata["document_number"] == "23/2008/QH12"  # _ → /
    assert docs[0].metadata["domain"] == "giao_thong"  # parent folder


def test_loader_handles_corrupt_meta_json(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "law.txt").write_text("body", encoding="utf-8")
    (raw_dir / "law.meta.json").write_text("{ not valid json", encoding="utf-8")
    loader = TxtDocumentLoader()
    docs = loader.load(raw_dir)  # should not raise
    assert len(docs) == 1
    assert docs[0].metadata["domain"] == "unknown"


def test_loader_skips_unknown_extensions(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "doc.txt").write_text("ok", encoding="utf-8")
    (raw_dir / "doc.bin").write_text("ignored", encoding="utf-8")
    docs = TxtDocumentLoader().load(raw_dir)
    assert len(docs) == 1


# ────────────────────────────────────────────────────────────────────────────
# Chunker — diagnostic
# ────────────────────────────────────────────────────────────────────────────


def test_parse_articles_returns_each_dieu() -> None:
    text = (
        "Tiêu đề luật\n\n"
        "Điều 1. Điều một\n"
        "Nội dung một.\n\n"
        "Điều 2. Điều hai\n"
        "Nội dung hai."
    )
    arts = parse_articles(text)
    assert [a.number for a in arts] == ["1", "2"]
    assert arts[0].title == "Điều một"
    assert "Nội dung một" in arts[0].body


def test_parse_articles_handles_no_articles() -> None:
    text = "Văn bản không có Điều nào, chỉ có text thuần."
    arts = parse_articles(text)
    assert len(arts) == 1
    assert arts[0].number == "0"
    assert arts[0].title == ""


# ────────────────────────────────────────────────────────────────────────────
# Chunker — structural splitting
# ────────────────────────────────────────────────────────────────────────────


def _doc(*, document_number: str = "23/2008/QH12", page_content: str = "") -> "object":
    from langchain_core.documents import Document

    return Document(
        page_content=page_content,
        metadata={
            "document_number": document_number,
            "document_title": "Test Law",
            "domain": "giao_thong",
            "source_url": "https://example/test",
        },
    )


def test_chunker_short_article_keeps_as_one_chunk() -> None:
    doc = _doc(page_content="Điều 1. Ngắn\nĐây là Điều ngắn gọn.")
    chunker = RecursiveVietnameseChunker(chunk_size=512, chunk_overlap=32)
    chunks = chunker.split([doc])
    assert len(chunks) == 1
    assert chunks[0].metadata["split_level"] == "article"
    assert chunks[0].metadata["article"] == "1"
    assert "ngắn gọn" in chunks[0].page_content.lower()


def test_chunker_long_article_splits_by_clause() -> None:
    body = "\n".join(f"{i}. Khoản {i}: nội dung dài để ép split." for i in range(1, 11))
    text = f"Điều 5. Nhiều khoản\n{body}"
    doc = _doc(page_content=text)
    chunker = RecursiveVietnameseChunker(chunk_size=120, chunk_overlap=10)
    chunks = chunker.split([doc])
    # Expect one chunk per clause
    assert len(chunks) == 10
    levels = {c.metadata["split_level"] for c in chunks}
    assert levels == {"clause"}
    # All chunks share the same article number
    assert {c.metadata["article"] for c in chunks} == {"5"}


def test_chunker_long_clause_splits_by_point() -> None:
    points = "\n".join(f"{c}) điểm {c} dài để ép split" for c in "abc")
    text = f"Điều 1. Test\n1. Khoản có nhiều điểm.\n{points}"
    doc = _doc(page_content=text)
    chunker = RecursiveVietnameseChunker(chunk_size=80, chunk_overlap=10)
    chunks = chunker.split([doc])
    # Each Điểm becomes one chunk with split_level="point"
    assert any(c.metadata["split_level"] == "point" for c in chunks)
    letters = [c.metadata["point"] for c in chunks if c.metadata["split_level"] == "point"]
    assert "a" in letters and "b" in letters and "c" in letters


def test_chunker_metadata_is_complete() -> None:
    doc = _doc(page_content=SAMPLE_TXT.read_text(encoding="utf-8"))
    chunker = RecursiveVietnameseChunker(chunk_size=256, chunk_overlap=32)
    chunks = chunker.split([doc])
    assert len(chunks) > 0
    for chunk in chunks:
        for key in REQUIRED_CHUNK_KEYS:
            assert key in chunk.metadata, f"Missing {key} in {chunk.metadata}"
        assert chunk.metadata["chunk_id"]  # non-empty uuid
        assert chunk.metadata["document_number"] == "23/2008/QH12"
        assert chunk.metadata["domain"] == "giao_thong"


def test_chunker_chunks_have_unique_ids() -> None:
    doc = _doc(page_content=SAMPLE_TXT.read_text(encoding="utf-8"))
    chunker = RecursiveVietnameseChunker(chunk_size=256, chunk_overlap=32)
    chunks = chunker.split([doc])
    ids = [c.metadata["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))


def test_chunker_includes_article_title_in_header() -> None:
    doc = _doc(page_content="Điều 7. Quy định về tốc độ\nTối đa 60 km/h trong đô thị.")
    chunker = RecursiveVietnameseChunker(chunk_size=512, chunk_overlap=32)
    chunks = chunker.split([doc])
    assert "Điều 7 — Quy định về tốc độ" in chunks[0].page_content


def test_chunker_preserves_leading_dai_character() -> None:
    """Regression: earlier bug stripped the leading 'Đ' from clause bodies."""
    doc = _doc(
        page_content=(
            "Điều 1. Test\n"
            "1. Đây là khoản đầu tiên có nội dung khá dài để ép split theo khoản."
        )
    )
    chunker = RecursiveVietnameseChunker(chunk_size=80, chunk_overlap=10)
    chunks = chunker.split([doc])
    # Inspect only chunks produced by clause-level splitting (split_level != 'article').
    clause_chunks = [c for c in chunks if c.metadata.get("split_level") != "article"]
    assert clause_chunks, "expected at least one clause-level chunk"
    text = "\n".join(c.page_content for c in clause_chunks)
    assert "Đây là khoản" in text
    # The bug manifested as a clause body beginning with "ây là khoản" — i.e.
    # the leading 'Đ' had been eaten by the regex's body-anchoring logic.
    # We check that no line in the clause body starts with the corrupted
    # substring.
    body_lines = [line for line in text.splitlines() if "khoản" in line.lower()]
    assert body_lines, "expected a khoản line in the clause body"
    assert not any(line.lstrip().startswith("ây là khoản") for line in body_lines)


def test_chunker_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError):
        RecursiveVietnameseChunker(chunk_size=0)
    with pytest.raises(ValueError):
        RecursiveVietnameseChunker(chunk_size=100, chunk_overlap=100)


# ────────────────────────────────────────────────────────────────────────────
# Pipeline end-to-end
# ────────────────────────────────────────────────────────────────────────────


def test_pipeline_run_ingestion_end_to_end(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "processed"

    domain_dir = raw_dir / "giao_thong"
    domain_dir.mkdir(parents=True)
    txt = (FIXTURES_DIR / "sample_law.txt").read_text(encoding="utf-8")
    meta = json.loads((FIXTURES_DIR / "sample_law.meta.json").read_text(encoding="utf-8"))
    (domain_dir / "23_2008.txt").write_text(txt, encoding="utf-8")
    (domain_dir / "23_2008.meta.json").write_text(json.dumps(meta), encoding="utf-8")

    loader = TxtDocumentLoader()
    chunker = RecursiveVietnameseChunker(chunk_size=256, chunk_overlap=32)

    written = run_ingestion(loader, chunker, raw_dir=raw_dir, out_dir=out_dir)
    assert len(written) == 1
    jsonl_path = written[0]
    assert jsonl_path.exists()

    lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) > 1
    record = json.loads(lines[0])
    assert "text" in record
    assert "metadata" in record
    for key in REQUIRED_CHUNK_KEYS:
        assert key in record["metadata"]


def test_pipeline_skips_missing_raw_dir(tmp_path: Path) -> None:
    loader = TxtDocumentLoader()
    chunker = RecursiveVietnameseChunker()
    result = run_ingestion(loader, chunker, raw_dir=tmp_path / "does_not_exist", out_dir=tmp_path)
    assert result == []


def test_collect_raw_files_filters_by_domain(tmp_path: Path) -> None:
    (tmp_path / "giao_thong").mkdir()
    (tmp_path / "dan_su").mkdir()
    (tmp_path / "giao_thong" / "a.txt").write_text("a")
    (tmp_path / "dan_su" / "b.txt").write_text("b")
    only_giao = collect_raw_files(raw_dir=tmp_path, domains=["giao_thong"])
    assert len(only_giao) == 1
    assert only_giao[0].name == "a.txt"


def test_raw_dir_exists_in_package() -> None:
    assert RAW_DIR.is_dir()
