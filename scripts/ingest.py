"""CLI: ingest raw documents into chunked JSONL.

Usage examples
--------------

    # Ingest every domain
    python scripts/ingest.py --all

    # Ingest a single domain
    python scripts/ingest.py giao_thong

    # Use fallback recursive chunker
    python scripts/ingest.py giao_thong --chunker recursive
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.domains import DOMAIN_REGISTRY
from vietnam_legal_rag.ingestion.chunker import (
    RecursiveVietnameseChunker,
    StructuralVietnameseChunker,
)
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import run_ingestion
from vietnam_legal_rag.paths import PROCESSED_DIR, RAW_DIR

app = typer.Typer(add_completion=False, help="Ingest scraped documents into chunks.")
console = Console()


def _resolve(domains: list[str], ingest_all: bool) -> list[str] | None:
    if ingest_all:
        return list(DOMAIN_REGISTRY.keys())
    if not domains:
        return None  # everything found in raw/
    unknown = [d for d in domains if d not in DOMAIN_REGISTRY]
    if unknown:
        raise typer.BadParameter(
            f"Unknown domain(s): {', '.join(unknown)}. "
            f"Known: {', '.join(sorted(DOMAIN_REGISTRY))}"
        )
    return domains


@app.command()
def main(
    domains: list[str] = typer.Argument(None, help="Domain name(s) to ingest."),
    all_domains: bool = typer.Option(False, "--all", help="Ingest every registered domain."),
    raw_dir: Path = typer.Option(RAW_DIR, "--raw-dir"),
    out_dir: Path = typer.Option(PROCESSED_DIR, "--out-dir"),
    chunker_type: str = typer.Option(
        "structural",
        "--chunker",
        help="Chunking strategy: 'structural' (SOTA) or 'recursive' (fallback).",
    ),
) -> None:
    """Run the ingestion pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    settings = get_settings()
    selected = _resolve(domains or [], all_domains)
    console.print("[bold]Vietnam Legal RAG — ingest[/bold]")
    console.print(f"Chunker:      {chunker_type}")
    console.print(f"Raw dir:      {raw_dir}")
    console.print(f"Processed:    {out_dir}")
    if selected:
        console.print(f"Domains:      {', '.join(selected)}")
    else:
        console.print("Domains:      (auto-detect from raw/ tree)")

    loader = TxtDocumentLoader()

    if chunker_type == "structural":
        chunker = StructuralVietnameseChunker(enrich_title=True)
    else:
        chunker = RecursiveVietnameseChunker(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )

    written = run_ingestion(
        loader, chunker, raw_dir=raw_dir, out_dir=out_dir, domains=selected
    )
    console.print(f"[green]Done. {len(written)} file(s) written.[/green]")


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
