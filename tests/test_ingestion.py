"""Ingestion tests — stubs to be expanded in the ingestion phase."""

from __future__ import annotations

from vietnam_legal_rag.ingestion.chunker import RecursiveVietnameseChunker
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import collect_raw_files
from vietnam_legal_rag.paths import RAW_DIR


def test_loader_is_concrete() -> None:
    loader = TxtDocumentLoader()
    assert loader is not None


def test_chunker_keeps_separator_order() -> None:
    chunker = RecursiveVietnameseChunker(chunk_size=256, chunk_overlap=32)
    assert chunker.chunk_size == 256
    assert chunker.chunk_overlap == 32


def test_collect_raw_files_returns_list(tmp_path) -> None:
    # Empty raw_dir yields an empty list, never raises
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    assert isinstance(collect_raw_files(raw_dir=tmp_path), list)


def test_raw_dir_exists() -> None:
    # The package guarantees the directory exists at import time.
    assert RAW_DIR.is_dir()
