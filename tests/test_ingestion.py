"""Ingestion tests — loader, chunker, enrichment, and pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.documents import Document

from vietnam_legal_rag.ingestion.chunker import (
    RecursiveVietnameseChunker,
    StructuralVietnameseChunker,
)
from vietnam_legal_rag.ingestion.enrichment import build_title_chain, enrich_chunk
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import collect_raw_files, run_ingestion
from vietnam_legal_rag.paths import RAW_DIR


# ── Sample legal text for testing ────────────────────────────────────────

SAMPLE_LEGAL_TEXT = """\
Chương I

QUY ĐỊNH CHUNG

Điều 1. Phạm vi điều chỉnh

1. Nghị định này quy định về hành vi vi phạm hành chính.

2. Các hành vi vi phạm hành chính khác áp dụng theo quy định khác.

Điều 2. Đối tượng áp dụng

1. Cá nhân, tổ chức có hành vi vi phạm.

Chương II

XỬ PHẠT VI PHẠM

Mục 1. Vi phạm quy tắc giao thông

Điều 5. Xử phạt người điều khiển xe ô tô

1. Phạt tiền từ 200.000 đồng đến 400.000 đồng:
a) Không chấp hành hiệu lệnh biển báo;
b) Không sử dụng đèn chiếu sáng.

2. Phạt tiền từ 3.000.000 đồng đến 5.000.000 đồng:
a) Vượt đèn đỏ;
b) Chạy quá tốc độ từ 10 km/h đến 20 km/h.
"""


# ── Loader tests ─────────────────────────────────────────────────────────


def test_loader_is_concrete() -> None:
    loader = TxtDocumentLoader()
    assert loader is not None


def test_loader_loads_txt_with_sidecar(tmp_path: Path) -> None:
    """Test loading a .txt file with its .meta.json sidecar."""
    txt = tmp_path / "test.txt"
    txt.write_text("Điều 1. Nội dung.", encoding="utf-8")
    meta = tmp_path / "test.meta.json"
    meta.write_text(
        json.dumps({"title": "Luật Test", "document_number": "01/2024/QH15"}),
        encoding="utf-8",
    )

    loader = TxtDocumentLoader()
    docs = loader.load(txt)
    assert len(docs) == 1
    assert docs[0].page_content == "Điều 1. Nội dung."
    assert docs[0].metadata["title"] == "Luật Test"
    assert docs[0].metadata["document_number"] == "01/2024/QH15"


def test_loader_loads_directory(tmp_path: Path) -> None:
    """Test loading all .txt files from a directory."""
    for i in range(3):
        (tmp_path / f"doc{i}.txt").write_text(f"Điều {i}.", encoding="utf-8")

    loader = TxtDocumentLoader()
    docs = loader.load(tmp_path)
    assert len(docs) == 3


def test_loader_handles_missing_sidecar(tmp_path: Path) -> None:
    """Loader should still work without .meta.json."""
    txt = tmp_path / "no_meta.txt"
    txt.write_text("Content without metadata.", encoding="utf-8")

    loader = TxtDocumentLoader()
    docs = loader.load(txt)
    assert len(docs) == 1
    assert docs[0].metadata.get("source_file") is not None


# ── Chunker tests ────────────────────────────────────────────────────────


def test_chunker_keeps_separator_order() -> None:
    chunker = RecursiveVietnameseChunker(chunk_size=256, chunk_overlap=32)
    assert chunker.chunk_size == 256
    assert chunker.chunk_overlap == 32


def test_structural_chunker_splits_by_dieu() -> None:
    """Structural chunker should produce chunks for each Khoản."""
    doc = Document(
        page_content=SAMPLE_LEGAL_TEXT,
        metadata={"document_number": "100/2019/NĐ-CP", "title": "NĐ Test"},
    )
    chunker = StructuralVietnameseChunker(enrich_title=False)
    chunks = chunker.split([doc])

    # Should have: Đ1K1, Đ1K2, Đ2K1, Đ5K1, Đ5K2 = 5 chunks
    assert len(chunks) >= 5

    # Check metadata on chunks
    articles = [c.metadata.get("article") for c in chunks]
    assert "1" in articles
    assert "2" in articles
    assert "5" in articles


def test_structural_chunker_preserves_khoan_content() -> None:
    """Each chunk should contain the full Khoản text."""
    doc = Document(
        page_content=SAMPLE_LEGAL_TEXT,
        metadata={"document_number": "TEST", "title": "Test"},
    )
    chunker = StructuralVietnameseChunker(enrich_title=False)
    chunks = chunker.split([doc])

    # Find the chunk for Điều 5, Khoản 2 (vượt đèn đỏ)
    dieu5_k2 = [c for c in chunks if c.metadata.get("article") == "5" and c.metadata.get("clause") == "2"]
    assert len(dieu5_k2) == 1
    assert "Vượt đèn đỏ" in dieu5_k2[0].page_content


def test_structural_chunker_assigns_chapter() -> None:
    """Chunks should have chapter/section metadata."""
    doc = Document(
        page_content=SAMPLE_LEGAL_TEXT,
        metadata={"document_number": "TEST", "title": "Test"},
    )
    chunker = StructuralVietnameseChunker(enrich_title=False)
    chunks = chunker.split([doc])

    # Điều 5 should be in Chương II
    dieu5 = [c for c in chunks if c.metadata.get("article") == "5"]
    assert len(dieu5) > 0
    assert "Chương II" in dieu5[0].metadata.get("chapter", "")


def test_structural_chunker_title_enrichment() -> None:
    """When enrich_title=True, chunks should have title_chain prepended."""
    doc = Document(
        page_content=SAMPLE_LEGAL_TEXT,
        metadata={"document_number": "TEST", "title": "NĐ Test"},
    )
    chunker = StructuralVietnameseChunker(enrich_title=True)
    chunks = chunker.split([doc])

    assert len(chunks) > 0
    first = chunks[0]
    assert "title_chain" in first.metadata
    assert first.page_content.startswith("[")  # Starts with title chain


# ── Enrichment tests ─────────────────────────────────────────────────────


def test_build_title_chain() -> None:
    meta = {
        "title": "Luật GTĐB",
        "chapter": "Chương II",
        "section": "Mục 1",
        "article": "5",
        "article_title": "Xử phạt xe ô tô",
    }
    chain = build_title_chain(meta)
    assert "[Luật GTĐB]" in chain
    assert "[Chương II]" in chain
    assert "[Điều 5. Xử phạt xe ô tô]" in chain


def test_enrich_chunk_prepends_title() -> None:
    chunk = Document(
        page_content="Phạt tiền 200.000 đồng.",
        metadata={"title": "Luật Test", "article": "1"},
    )
    enriched = enrich_chunk(chunk)
    assert enriched.page_content.startswith("[Luật Test]")
    assert "Phạt tiền 200.000 đồng." in enriched.page_content


# ── Pipeline tests ───────────────────────────────────────────────────────


def test_collect_raw_files_returns_list(tmp_path: Path) -> None:
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    assert isinstance(collect_raw_files(raw_dir=tmp_path), list)


def test_raw_dir_exists() -> None:
    assert RAW_DIR.is_dir()


def test_full_pipeline(tmp_path: Path) -> None:
    """End-to-end: raw .txt → JSONL chunks."""
    # Setup raw data
    domain_dir = tmp_path / "raw" / "test_domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "doc.txt").write_text(SAMPLE_LEGAL_TEXT, encoding="utf-8")
    (domain_dir / "doc.meta.json").write_text(
        json.dumps({"title": "NĐ Test", "document_number": "TEST/2024"}),
        encoding="utf-8",
    )

    out_dir = tmp_path / "processed"
    loader = TxtDocumentLoader()
    chunker = StructuralVietnameseChunker(enrich_title=True)

    written = run_ingestion(
        loader,
        chunker,
        raw_dir=tmp_path / "raw",
        out_dir=out_dir,
        domains=["test_domain"],
    )

    assert len(written) == 1
    assert written[0].suffix == ".jsonl"

    # Verify JSONL content
    lines = written[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 5  # At least 5 chunks

    first = json.loads(lines[0])
    assert "text" in first
    assert "metadata" in first
    assert first["metadata"]["document_number"] == "TEST/2024"
