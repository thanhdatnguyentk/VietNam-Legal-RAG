"""CLI: build the ChromaDB index from processed chunks.

Usage
-----

    python scripts/build_index.py
    python scripts/build_index.py --processed-dir data/processed --reset
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.paths import PROCESSED_DIR
from vietnam_legal_rag.vectorstore.chroma import VectorStore

app = typer.Typer(add_completion=False, help="Build / refresh the vector index.")
console = Console()


@app.command()
def main(
    processed_dir: Path = typer.Option(PROCESSED_DIR, "--processed-dir"),
    reset: bool = typer.Option(False, "--reset", help="Drop the existing collection first."),
) -> None:
    """Embed processed chunks and upsert them into ChromaDB."""
    settings = get_settings()
    console.print(f"[bold]Vietnam Legal RAG — build_index[/bold]")
    console.print(f"Embedding:        {settings.embedding_model} ({settings.embedding_device})")
    console.print(f"Chroma persist:   {settings.chroma_persist_dir}")
    console.print(f"Chroma collection:{settings.chroma_collection_name}")
    console.print(f"Processed dir:    {processed_dir}")
    console.print(f"Reset collection: {reset}")

    embedder = VietnameseEmbedder()
    store = VectorStore()

    # SKELETON — both embedder and store raise NotImplementedError on use.
    _ = embedder
    _ = store
    raise NotImplementedError(
        "build_index.py is a skeleton — see docs/roadmap.md for the next phase."
    )


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
