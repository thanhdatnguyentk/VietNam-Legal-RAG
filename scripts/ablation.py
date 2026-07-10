"""Full ablation study including Reranked Hybrid configuration."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from vietnam_legal_rag.eval.evaluator import BaselineRetrieverEvaluator
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever, RerankedHybridRetriever
from vietnam_legal_rag.vectorstore.chroma import VectorStore
from vietnam_legal_rag.config import get_settings

app = typer.Typer()
console = Console()

@app.command()
def main(
    testset: str = typer.Option("data/eval/questions.v2.jsonl", "--testset"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    include_reranker: bool = typer.Option(False, "--reranker", help="Include Reranked Hybrid (slower)"),
) -> None:
    testset_path = Path(testset)
    if not testset_path.exists():
        console.print(f"[red]Error: Testset not found at {testset_path}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold blue]🏛️ Vietnam Legal RAG — Full Ablation Study[/bold blue]")
    
    # Initialize shared components
    settings = get_settings()
    console.print("Loading models and indexes...")
    embedder = VietnameseEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)
    store = VectorStore()
    
    dense_retriever = DenseRetriever(embedder=embedder, store=store, top_k=top_k)
    
    bm25_retriever = BM25Retriever()
    bm25_retriever._load()

    # Define experiments
    experiments = [
        {"name": "Dense-Only", "retriever": dense_retriever},
        {"name": "BM25-Only", "retriever": bm25_retriever},
        {"name": "Hybrid (D=0.3, B=0.7)", "retriever": HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.3, bm25_weight=0.7)},
        {"name": "Hybrid (D=0.5, B=0.5)", "retriever": HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.5, bm25_weight=0.5)},
        {"name": "Hybrid (D=0.6, B=0.4)", "retriever": HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.6, bm25_weight=0.4)},
        {"name": "Hybrid (D=0.7, B=0.3)", "retriever": HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.7, bm25_weight=0.3)},
        {"name": "Hybrid (D=0.8, B=0.2)", "retriever": HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.8, bm25_weight=0.2)},
    ]

    if include_reranker:
        experiments.append({
            "name": "Hybrid+Reranker (D=0.5, B=0.5, Top50→5)",
            "retriever": RerankedHybridRetriever(
                dense_retriever, bm25_retriever,
                dense_weight=0.5, bm25_weight=0.5,
                stage1_candidates=50,
            ),
        })
        experiments.append({
            "name": "Hybrid+Reranker (D=0.3, B=0.7, Top50→5)",
            "retriever": RerankedHybridRetriever(
                dense_retriever, bm25_retriever,
                dense_weight=0.3, bm25_weight=0.7,
                stage1_candidates=50,
            ),
        })

    results = []

    for exp in experiments:
        console.print(f"\n[cyan]Running: {exp['name']}[/cyan]")
        evaluator = BaselineRetrieverEvaluator(retriever=exp["retriever"], testset_path=testset_path, top_k=top_k)
        
        with console.status("Evaluating..."):
            report = evaluator.run()
            results.append((exp["name"], report))
        console.print(f"  → Recall@{top_k} = {report.retrieval_recall_at_k:.2%}")

    # Print comparative table
    table = Table(title=f"Ablation Results (Top-{top_k})")
    table.add_column("Configuration", style="cyan")
    table.add_column("Precision", justify="right", style="magenta")
    table.add_column("Recall", justify="right", style="green")

    best_recall = 0
    best_name = ""
    for name, report in results:
        table.add_row(name, f"{report.retrieval_precision_at_k:.2%}", f"{report.retrieval_recall_at_k:.2%}")
        if report.retrieval_recall_at_k > best_recall:
            best_recall = report.retrieval_recall_at_k
            best_name = name

    console.print("\n")
    console.print(table)
    console.print(f"\n[bold green]🏆 Best: {best_name} (Recall@{top_k} = {best_recall:.2%})[/bold green]")
    
    # Save results
    out_path = Path("docs/ablation_results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Ablation Study Results (Top-{top_k})\n\n")
        f.write(f"**Date**: 2026-07-10 | **Testset**: {testset_path}\n\n")
        f.write("| Configuration | Precision | Recall |\n|---|---|---|\n")
        for name, report in results:
            f.write(f"| {name} | {report.retrieval_precision_at_k:.2%} | {report.retrieval_recall_at_k:.2%} |\n")
        f.write(f"\n**Best**: {best_name} → Recall@{top_k} = {best_recall:.2%}\n")
    
    console.print(f"[green]✅ Results saved to {out_path}[/green]")

if __name__ == "__main__":
    app()
