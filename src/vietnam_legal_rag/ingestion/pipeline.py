"""Top-level ingestion orchestrator.

Reads ``data/raw/``, chunks everything, and writes a JSONL file per source
document into ``data/processed/``. The resulting JSONL is the stable input
for the embedding stage, so the format must not change without a version
bump (see :mod:`docs/data-model.md`).
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


def collect_raw_files(
    raw_dir: Path = RAW_DIR,
    domains: Iterable[str] | None = None,
) -> list[Path]:
    """Return raw files in ``raw_dir``, optionally filtered by domain subfolder.

    Domains are matched against the path's parent directory name (e.g.
    ``data/raw/giao_thong/23_2008.txt`` → ``domain="giao_thong"``).
    Pass ``None`` to autodetect everything.
    """
    if not raw_dir.exists():
        return []
    if domains is None:
        return sorted(
            p for p in raw_dir.glob("**/*") if p.is_file() and p.suffix in {".txt", ".md"}
        )
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
    overwrite: bool = True,
) -> list[Path]:
    """Load → chunk → write JSONL; return the list of files written.

    Args:
        loader: anything implementing :class:`DocumentLoader`.
        chunker: anything implementing :class:`TextChunker`.
        raw_dir: directory holding the ``.txt`` + ``.meta.json`` pairs.
        out_dir: directory where the JSONL outputs are written.
        domains: optional iterable of domain names to filter on; ``None``
            means process every ``.txt`` under ``raw_dir``.
        overwrite: when False, skip files whose output already exists.
    """
    settings = get_settings()
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_files = collect_raw_files(raw_dir=raw_dir, domains=domains)
    if not raw_files:
        logger.warning("No raw files found under %s (domains=%s)", raw_dir, domains)
        return []

    logger.info(
        "Starting ingestion: %d file(s) → %s (chunk_size=%d, overlap=%d)",
        len(raw_files),
        out_dir,
        settings.chunk_size,
        settings.chunk_overlap,
    )

    written: list[Path] = []
    total_chunks = 0
    for raw_file in raw_files:
        out_path = out_dir / f"{raw_file.stem}.chunks.jsonl"
        if out_path.exists() and not overwrite:
            logger.info("Skipping %s (exists; use overwrite=True to refresh)", raw_path_safe(raw_file))
            continue
        try:
            docs: list[Document] = loader.load(raw_file)
        except Exception as exc:
            logger.error("Loader failed on %s: %s", raw_file, exc)
            continue

        if not docs:
            logger.warning("Loader returned 0 docs for %s — skipping", raw_file)
            continue

        chunks = chunker.split(docs)
        total_chunks += len(chunks)
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
        logger.info("  %s → %d chunks", raw_file.name, len(chunks))

    logger.info(
        "Ingestion complete: %d file(s) → %d chunk(s) total", len(written), total_chunks
    )
    return written


def raw_path_safe(p: Path) -> str:
    """Format a raw path short enough for logging on slow terminals."""
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)


__all__ = ["collect_raw_files", "run_ingestion"]
