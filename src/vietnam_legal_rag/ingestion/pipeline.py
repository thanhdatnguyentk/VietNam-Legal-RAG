"""Top-level ingestion orchestrator.

Reads ``data/raw/``, chunks everything, and writes a JSONL file per domain
into ``data/processed/``. The resulting JSONL is what the embedding stage
consumes, so the format must stay stable across versions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.ingestion.chunker import TextChunker
from vietnam_legal_rag.ingestion.loader import DocumentLoader
from vietnam_legal_rag.paths import PROCESSED_DIR, RAW_DIR


def collect_raw_files(raw_dir: Path = RAW_DIR, domains: Iterable[str] | None = None) -> list[Path]:
    """Return raw files in ``raw_dir``, optionally filtered by domain subfolder."""
    if not raw_dir.exists():
        return []
    if domains is None:
        return sorted(p for p in raw_dir.glob("**/*") if p.is_file() and p.suffix in {".txt", ".md"})
    return sorted(
        p
        for d in domains
        for p in (raw_dir / d).glob("**/*")
        if p.is_file() and p.suffix in {".txt", ".md"}
    )


def run_ingestion(
    loader: DocumentLoader,
    chunker: TextChunker,
    *,
    raw_dir: Path = RAW_DIR,
    out_dir: Path = PROCESSED_DIR,
    domains: Iterable[str] | None = None,
) -> list[Path]:
    """Load → chunk → write JSONL; return the list of files written.

    SKELETON — wires up the interfaces but does not yet iterate over files.
    """
    settings = get_settings()
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_files = collect_raw_files(raw_dir=raw_dir, domains=domains)
    written: list[Path] = []
    for raw_file in raw_files:
        docs: list[Document] = loader.load(raw_file)
        chunks: list[Document] = chunker.split(docs)
        out_path = out_dir / f"{raw_file.stem}.chunks.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for chunk in chunks:
                fh.write(
                    json.dumps(
                        {"text": chunk.page_content, "metadata": chunk.metadata},
                        ensure_ascii=False,
                    )
                )
                fh.write("\n")
        written.append(out_path)
    _ = settings  # silence unused until implementation wires it up
    return written


__all__ = ["collect_raw_files", "run_ingestion"]
