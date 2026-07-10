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

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.domains import DOMAIN_REGISTRY
from vietnam_legal_rag.paths import RAW_DIR
from vietnam_legal_rag.scrapers.thuvienphapluat import ThuvienPhapLuatScraper

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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    settings = get_settings()
    selected = _resolve_targets(domains or [], all_domains)
    console.print("[bold]Vietnam Legal RAG — scraper[/bold]")
    console.print(f"Selected domains: {', '.join(selected)}")
    console.print(f"Output dir:        {out_dir}")
    console.print(f"Base URL:          {settings.scraper_base_url}")

    if dry_run:
        for name in selected:
            spec = DOMAIN_REGISTRY[name]
            console.print(f"  - {name} ({len(spec.source_urls)} URLs)")
            for url in spec.source_urls:
                console.print(f"    → {url}")
        console.print("[yellow]Dry-run only — no network requests issued.[/yellow]")
        return

    # Initialize scraper
    scraper = ThuvienPhapLuatScraper(
        base_url=settings.scraper_base_url,
        user_agent=settings.scraper_user_agent,
        timeout=settings.scraper_request_timeout,
        rate_limit_seconds=settings.scraper_rate_limit_seconds,
    )

    total_saved = 0
    for name in selected:
        spec = DOMAIN_REGISTRY[name]
        domain_dir = out_dir / name
        console.print(f"\n[bold blue]Domain: {spec.display_name}[/bold blue]")

        if not spec.source_urls:
            console.print(f"  [yellow]No source URLs configured for {name}[/yellow]")
            continue

        saved = scraper.run(spec.source_urls, domain_dir)
        total_saved += len(saved)
        for path in saved:
            console.print(f"  ✓ {path.name}")

    console.print(f"\n[green]Done. {total_saved} document(s) saved.[/green]")


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
