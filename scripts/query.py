"""CLI: interactive legal query tool.

Usage
-----

    python scripts/query.py "mức phạt vượt đèn đỏ"
    python scripts/query.py "quy định về hợp đồng lao động" --domain lao_dong
    python scripts/query.py --interactive
    python scripts/query.py --interactive --rag
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever
from vietnam_legal_rag.vectorstore.chroma import VectorStore
from vietnam_legal_rag.generation.llm import build_default_llm
from vietnam_legal_rag.pipeline.rag import RAGPipeline

app = typer.Typer(add_completion=False, help="Query the legal knowledge base.")
console = Console()


def format_hit(hit, idx: int) -> Panel:
    """Format a single retrieval hit as a Rich panel."""
    meta = hit.document.metadata
    doc_num = meta.get("document_number", "?")
    article = meta.get("article", "?")
    clause = meta.get("clause", "")
    title = meta.get("title", "")[:80]
    domain = meta.get("domain", "")
    score = hit.score

    header = f"[bold cyan]#{idx}[/bold cyan] | Score: [green]{score:.3f}[/green] | {doc_num}"
    if article != "?":
        header += f" Điều {article}"
    if clause:
        header += f" Khoản {clause}"

    content = hit.document.page_content[:500]
    if len(hit.document.page_content) > 500:
        content += "\n[dim]...(truncated)[/dim]"

    subtitle = f"[dim]{domain} | {title}[/dim]"

    return Panel(content, title=header, subtitle=subtitle, border_style="blue")


@app.command()
def main(
    query: str = typer.Argument(None, help="Query text"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    domain: str = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
    rag: bool = typer.Option(False, "--rag", "-r", help="Use full RAG pipeline (LLM generation)"),
    hybrid: bool = typer.Option(False, "--hybrid", help="Use hybrid retrieval (BM25 + Dense)"),
    model: str = typer.Option(None, "--model", help="Override embedding model"),
) -> None:
    """Search the legal knowledge base."""
    settings = get_settings()

    console.print("[bold]🏛️ Vietnam Legal RAG — Query[/bold]\n")

    # Initialize Retrieval components
    console.print("[blue]Initializing Retrievers...[/blue]")
    embedder = VietnameseEmbedder(model_name=model)
    store = VectorStore()

    vec_count = store.count()
    if vec_count == 0:
        console.print("[red]No vectors in index. Run build_index.py first.[/red]")
        sys.exit(1)

    console.print(f"  Index: {vec_count:,} vectors | Model: {embedder.model_name}")

    dense_retriever = DenseRetriever(embedder=embedder, store=store, top_k=top_k)
    
    if hybrid:
        console.print("  Loading BM25 index...")
        bm25_retriever = BM25Retriever()
        bm25_retriever._load() # Preload
        retriever = HybridRetriever(dense_retriever, bm25_retriever)
        console.print("  [green]Hybrid retrieval active.[/green]")
    else:
        retriever = dense_retriever

    # Initialize RAG Pipeline if requested
    pipeline = None
    if rag:
        console.print(f"  [blue]Initializing LLM ({settings.llm_provider})...[/blue]")
        try:
            llm = build_default_llm()
            pipeline = RAGPipeline(retriever=retriever, llm=llm)
            console.print("  [green]RAG Pipeline active.[/green]")
        except Exception as e:
            console.print(f"[red]Error initializing LLM: {e}[/red]")
            sys.exit(1)

    console.print()

    def process_query(q: str):
        if pipeline:
            with console.status(f"[bold green]Generating answer...[/bold green]"):
                answer = pipeline.query(q, domain=domain)
            
            console.print(Panel(Markdown(answer.answer), title="[bold yellow]RAG Answer[/bold yellow]", border_style="yellow"))
            console.print("\n[bold]Retrieved Sources:[/bold]")
            for i, hit in enumerate(answer.hits[:top_k], 1):
                console.print(format_hit(hit, i))
        else:
            with console.status(f"[bold green]Searching...[/bold green]"):
                hits = retriever.retrieve(q, top_k=top_k, domain=domain) if not hybrid else retriever.retrieve(q, top_k=top_k, domain=domain)
            console.print(f"Results for: [bold]\"{q}\"[/bold]")
            if domain:
                console.print(f"Domain filter: [cyan]{domain}[/cyan]")
            console.print()

            for i, hit in enumerate(hits, 1):
                console.print(format_hit(hit, i))
            console.print()

    if interactive:
        console.print("[yellow]Interactive mode. Type 'quit' to exit.[/yellow]\n")
        while True:
            try:
                q = console.input("[bold green]Query >[/bold green] ")
            except (KeyboardInterrupt, EOFError):
                break
            if q.strip().lower() in ("quit", "exit", "q"):
                break
            if not q.strip():
                continue
            
            process_query(q.strip())
            
    else:
        if not query:
            console.print("[red]Provide a query or use --interactive mode.[/red]")
            sys.exit(1)

        process_query(query)


if __name__ == "__main__":
    app()
