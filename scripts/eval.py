"""CLI: run evaluation on the retrieval and generation pipeline."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from vietnam_legal_rag.eval.evaluator import BaselineRetrieverEvaluator
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.vectorstore.chroma import VectorStore
from vietnam_legal_rag.config import get_settings

from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever

app = typer.Typer(add_completion=False, help="Evaluate the system.")
console = Console()

@app.command()
def main(
    testset: str = typer.Option("data/eval/questions.v1.jsonl", "--testset", help="Path to JSONL testset"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of retrieved chunks to evaluate"),
    hybrid: bool = typer.Option(False, "--hybrid", help="Use hybrid retrieval (BM25 + Dense)"),
) -> None:
    """Run evaluation and output metrics."""
    testset_path = Path(testset)
    if not testset_path.exists():
        console.print(f"[red]Error: Testset not found at {testset_path}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]🏛️ Vietnam Legal RAG — Evaluation[/bold blue]")
    console.print(f"Loading testset: {testset_path}")
    
    settings = get_settings()
    console.print(f"Initializing DenseRetriever with model: {settings.embedding_model}")
    embedder = VietnameseEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)
    store = VectorStore()
    dense_retriever = DenseRetriever(embedder=embedder, store=store, top_k=top_k)

    if hybrid:
        console.print("Loading BM25 index... (this may take a moment)")
        bm25_retriever = BM25Retriever()
        bm25_retriever._load()
        retriever = HybridRetriever(dense_retriever, bm25_retriever)
        console.print("[green]Hybrid retrieval active.[/green]")
    else:
        retriever = dense_retriever

    evaluator = BaselineRetrieverEvaluator(retriever=retriever, testset_path=testset_path, top_k=top_k)
    
    with console.status("[bold green]Evaluating queries..."):
        report = evaluator.run()

    # Print results
    table_title = "Evaluation Results (Hybrid Retrieval)" if hybrid else "Evaluation Results (Baseline Dense Retrieval)"
    table = Table(title=table_title)
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right", style="magenta")
    
    table.add_row("Total Queries", str(report.total))
    table.add_row(f"Precision@{top_k}", f"{report.retrieval_precision_at_k:.2%}")
    table.add_row(f"Recall@{top_k}", f"{report.retrieval_recall_at_k:.2%}")
    
    console.print(table)
    
    if report.retrieval_recall_at_k >= 0.70:
        console.print("[bold green]✅ Baseline target met (Recall >= 70%)[/bold green]")
    else:
        console.print("[bold yellow]⚠️ Baseline target not met (Requires Hybrid/Reranker)[/bold yellow]")

if __name__ == "__main__":
    app()
