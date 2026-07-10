"""Top-level ingestion orchestrator.

Reads ``data/raw/``, chunks everything, and writes a JSONL file per domain
into ``data/processed/``. The resulting JSONL is what the embedding stage
consumes, so the format must stay stable across versions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.ingestion.chunker import TextChunker
from vietnam_legal_rag.ingestion.loader import DocumentLoader
from vietnam_legal_rag.paths import PROCESSED_DIR, RAW_DIR

logger = logging.getLogger(__name__)


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

    Each raw file produces a corresponding ``.chunks.jsonl`` file in
    ``out_dir``.  The JSONL format is one JSON object per line with
    ``text`` and ``metadata`` keys.
    """
    settings = get_settings()
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_files = collect_raw_files(raw_dir=raw_dir, domains=domains)
    if not raw_files:
        logger.warning("No raw files found in %s (domains=%s)", raw_dir, domains)
        return []

    logger.info("Found %d raw files to ingest", len(raw_files))
    written: list[Path] = []
    total_chunks = 0

    for raw_file in raw_files:
        logger.info("Processing: %s", raw_file.name)

        # Load
        docs: list[Document] = loader.load(raw_file)
        if not docs:
            logger.warning("Loader returned 0 documents for %s", raw_file)
            continue

        # Chunk
        chunks: list[Document] = chunker.split(docs)
        if not chunks:
            logger.warning("Chunker returned 0 chunks for %s", raw_file)
            continue

        logger.info("  → %d chunks from %s", len(chunks), raw_file.name)
        total_chunks += len(chunks)

        # Write JSONL
        # Preserve domain subfolder structure
        domain = raw_file.parent.name
        domain_out = out_dir / domain
        domain_out.mkdir(parents=True, exist_ok=True)

        out_path = domain_out / f"{raw_file.stem}.chunks.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for chunk in chunks:
                record = {
                    "text": chunk.page_content,
                    "metadata": chunk.metadata,
                }
                fh.write(json.dumps(record, ensure_ascii=False))
                fh.write("\n")
        written.append(out_path)

    logger.info(
        "Ingestion complete: %d files → %d chunks → %d JSONL files",
        len(raw_files),
        total_chunks,
        len(written),
    )
    _ = settings  # will be used for configurable chunking strategy
    return written


__all__ = ["collect_raw_files", "run_ingestion"]
