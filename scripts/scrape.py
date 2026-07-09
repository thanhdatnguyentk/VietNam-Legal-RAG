"""CLI: scrape Vietnamese legal documents from configured sources.

Usage examples
--------------

    # Scrape every domain registered in vietnam_legal_rag.domains
    python scripts/scrape.py --all

    # Scrape a single domain
    python scripts/scrape.py giao_thong

    # Dry-run (print URLs only, no network)
    python scripts/scrape.py --all --dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.domains import DOMAIN_REGISTRY
from vietnam_legal_rag.paths import RAW_DIR

app = typer.Typer(add_completion=False, help="Scrape Vietnamese legal documents.")
console = Console()


def _resolve_targets(targets: list[str], scrape_all: bool) -> list[str]:
    if scrape_all:
        return list(DOMAIN_REGISTRY.keys())
    if not targets:
        raise typer.BadParameter("Pass a domain name or use --all")
    unknown = [t for t in targets if t not in DOMAIN_REGISTRY]
    if unknown:
        raise typer.BadParameter(
            f"Unknown domain(s): {', '.join(unknown)}. "
            f"Known: {', '.join(sorted(DOMAIN_REGISTRY))}"
        )
    return targets


@app.command()
def main(
    domains: list[str] = typer.Argument(
        None,
        help="Domain name(s) to scrape. Use --all to scrape every registered domain.",
    ),
    all_domains: bool = typer.Option(False, "--all", help="Scrape every registered domain."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be done, do not hit the network."
    ),
    out_dir: Path = typer.Option(RAW_DIR, "--out-dir", help="Where to write scraped files."),
) -> None:
    """Scrape the selected domain(s) and persist raw files."""
    settings = get_settings()
    selected = _resolve_targets(domains or [], all_domains)
    console.print(f"[bold]Vietnam Legal RAG — scraper[/bold]")
    console.print(f"Selected domains: {', '.join(selected)}")
    console.print(f"Output dir:        {out_dir}")
    console.print(f"Base URL:          {settings.scraper_base_url}")

    if dry_run:
        for name in selected:
            spec = DOMAIN_REGISTRY[name]
            console.print(f"  - {name} ({len(spec.source_urls)} URLs)")
        console.print("[yellow]Dry-run only — no network requests issued.[/yellow]")
        return

    # ── SKELETON ────────────────────────────────────────────────────────────
    # The real scraper body is intentionally not implemented yet. Wiring plan:
    #   1. instantiate ThuvienPhapLuatScraper(settings)
    #   2. for each domain: collect detail URLs from spec.source_urls, then run()
    #   3. save into out_dir / spec.name
    raise NotImplementedError(
        "scrape.py is a skeleton — see docs/roadmap.md for the next phase."
    )


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
