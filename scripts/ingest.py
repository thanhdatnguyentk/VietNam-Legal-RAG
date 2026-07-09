"""CLI: ingest raw documents into chunked JSONL.

Usage examples
--------------

    # Ingest every domain
    python scripts/ingest.py --all

    # Ingest a single domain
    python scripts/ingest.py giao_thong

    # Dry run (print what would be ingested, write nothing)
    python scripts/ingest.py --all --dry-run
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.domains import DOMAIN_REGISTRY
from vietnam_legal_rag.ingestion.chunker import RecursiveVietnameseChunker
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import collect_raw_files, run_ingestion
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
    dry_run: bool = typer.Option(
        False, "--dry-run", help="List files that would be processed, then exit."
    ),
    stats: bool = typer.Option(False, "--stats", help="Print per-file chunk counts at the end."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
) -> None:
    """Run the ingestion pipeline."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    settings = get_settings()
    selected = _resolve(domains or [], all_domains)

    console.print("[bold]Vietnam Legal RAG — ingest[/bold]")
    console.print(f"Chunk size:   {settings.chunk_size} (overlap {settings.chunk_overlap})")
    console.print(f"Raw dir:      {raw_dir}")
    console.print(f"Processed:    {out_dir}")
    if selected:
        console.print(f"Domains:      {', '.join(selected)}")
    else:
        console.print("Domains:      (auto-detect from raw/ tree)")

    files = collect_raw_files(raw_dir=raw_dir, domains=selected)
    if not files:
        console.print("[yellow]No raw files found — nothing to ingest.[/yellow]")
        return

    if dry_run:
        table = Table(title="Files that would be ingested", show_lines=False)
        table.add_column("Domain", style="cyan")
        table.add_column("File", style="white")
        for f in files:
            domain = f.parent.name if f.parent != raw_dir else "?"
            table.add_row(domain, str(f.relative_to(raw_dir)))
        console.print(table)
        console.print(f"[yellow]Dry-run: {len(files)} file(s) — no output written.[/yellow]")
        return

    loader = TxtDocumentLoader()
    chunker = RecursiveVietnameseChunker(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )

    written = run_ingestion(loader, chunker, raw_dir=raw_dir, out_dir=out_dir, domains=selected)

    if stats and written:
        # Re-read the JSONL to count chunks; cheap because chunks are small.
        table = Table(title="Per-file chunk counts", show_lines=False)
        table.add_column("Output", style="cyan")
        table.add_column("Chunks", justify="right", style="green")
        total = 0
        for p in written:
            n = sum(1 for _ in p.open(encoding="utf-8"))
            total += n
            table.add_row(p.name, str(n))
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")
        console.print(table)

    console.print(f"[green]Done — {len(written)} file(s) written to {out_dir}.[/green]")


if __name__ == "__main__":
    try:
        app()
    except Exception as exc:  # surface a readable trace instead of exiting silently
        console.print(f"[red]Ingestion failed:[/red] {exc}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            raise
        sys.exit(1)