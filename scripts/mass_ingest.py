"""Mass ingest: process all crawled documents into chunks.

Usage:
    python scripts/mass_ingest.py              # All domains
    python scripts/mass_ingest.py --stats      # Show statistics only
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from vietnam_legal_rag.ingestion.chunker import StructuralVietnameseChunker, RecursiveVietnameseChunker
from vietnam_legal_rag.ingestion.loader import TxtDocumentLoader
from vietnam_legal_rag.ingestion.pipeline import run_ingestion
from vietnam_legal_rag.paths import PROCESSED_DIR, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Mass ingest crawled documents.")
console = Console()


def count_stats(base_dir: Path) -> dict:
    """Count documents and chunks across all domains."""
    stats = {}
    for domain_dir in sorted(base_dir.iterdir()):
        if domain_dir.is_dir() and domain_dir.name != ".gitkeep":
            txt_files = list(domain_dir.glob("*.txt"))
            stats[domain_dir.name] = len(txt_files)
    return stats


@app.command()
def main(
    stats_only: bool = typer.Option(False, "--stats", help="Show statistics only"),
    chunker_type: str = typer.Option("structural", "--chunker", help="structural or recursive"),
    raw_dir: Path = typer.Option(RAW_DIR, "--raw-dir"),
    out_dir: Path = typer.Option(PROCESSED_DIR, "--out-dir"),
) -> None:
    """Process all crawled documents into chunks."""
    console.print("[bold]🏛️ Vietnam Legal RAG — Mass Ingest[/bold]\n")

    # Show raw data stats
    raw_stats = count_stats(raw_dir)
    total_raw = sum(raw_stats.values())

    table = Table(title="📊 Raw Documents")
    table.add_column("Domain", style="cyan")
    table.add_column("Documents", justify="right", style="green")
    for domain, count in sorted(raw_stats.items(), key=lambda x: -x[1]):
        table.add_row(domain, str(count))
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_raw}[/bold]")
    console.print(table)

    if stats_only:
        # Also show processed stats
        proc_stats = {}
        for domain_dir in sorted(out_dir.iterdir()) if out_dir.exists() else []:
            if domain_dir.is_dir():
                chunks = 0
                for jsonl in domain_dir.glob("*.jsonl"):
                    chunks += sum(1 for _ in jsonl.open())
                if chunks:
                    proc_stats[domain_dir.name] = chunks

        if proc_stats:
            console.print()
            table2 = Table(title="📊 Processed Chunks")
            table2.add_column("Domain", style="cyan")
            table2.add_column("Chunks", justify="right", style="green")
            total_chunks = 0
            for domain, count in sorted(proc_stats.items(), key=lambda x: -x[1]):
                table2.add_row(domain, str(count))
                total_chunks += count
            table2.add_row("[bold]TOTAL[/bold]", f"[bold]{total_chunks}[/bold]")
            console.print(table2)
        return

    if total_raw == 0:
        console.print("[red]No raw documents found. Run mass_crawl.py first.[/red]")
        sys.exit(1)

    console.print(f"\nProcessing {total_raw} documents with '{chunker_type}' chunker...\n")

    loader = TxtDocumentLoader()
    if chunker_type == "structural":
        chunker = StructuralVietnameseChunker(enrich_title=True)
    else:
        chunker = RecursiveVietnameseChunker(chunk_size=512, chunk_overlap=64)

    written = run_ingestion(loader, chunker, raw_dir=raw_dir, out_dir=out_dir)

    # Count total chunks
    total_chunks = 0
    for f in written:
        total_chunks += sum(1 for _ in f.open())

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"  Documents processed: {total_raw}")
    console.print(f"  JSONL files written: {len(written)}")
    console.print(f"  Total chunks:        {total_chunks}")


if __name__ == "__main__":
    app()
