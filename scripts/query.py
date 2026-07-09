"""CLI: ask a question against the RAG pipeline.

Usage
-----

    # One-shot question
    python scripts/query.py "Điều kiện cấp GPLX hạng B1 là gì?"

    # Interactive REPL
    python scripts/query.py --interactive
"""

from __future__ import annotations

import sys

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.generation.llm import build_default_llm
from vietnam_legal_rag.pipeline.rag import RAGPipeline
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.vectorstore.chroma import VectorStore

app = typer.Typer(add_completion=False, help="Ask a question against the RAG pipeline.")
console = Console()


def _build_pipeline() -> RAGPipeline:  # pragma: no cover - skeleton
    """Construct a pipeline from the project's current state."""
    settings = get_settings()
    store = VectorStore()
    # The dense retriever expects a VietnameseEmbedder; both are skeletons.
    from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder

    embedder = VietnameseEmbedder()
    retriever = DenseRetriever(embedder=embedder, store=store, top_k=settings.retrieval_k)
    llm = build_default_llm()
    return RAGPipeline(retriever=retriever, llm=llm)


@app.command()
def main(
    question: str = typer.Argument(None, help="The question to ask. Omit for --interactive."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start a REPL."),
) -> None:
    """Run a single query, or start an interactive session."""
    settings = get_settings()
    console.print(f"[bold]Vietnam Legal RAG — query[/bold]")
    console.print(f"Model: {settings.llm_provider}/{settings.llm_model}")

    pipeline = _build_pipeline()

    if interactive:
        console.print("Type 'exit' or Ctrl-D to quit.")
        while True:
            try:
                q = console.input("[bold cyan]?> [/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                console.print("\nBye.")
                return
            if q.strip().lower() in {"exit", "quit"}:
                return
            if not q.strip():
                continue
            _ = pipeline.query(q)
            raise NotImplementedError("RAGPipeline.query is a skeleton.")

    if not question:
        raise typer.BadParameter("Pass a question, or use --interactive.")
    raise NotImplementedError("RAGPipeline.query is a skeleton — see docs/roadmap.md.")


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
