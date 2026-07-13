"""Run End-to-End LLM-as-a-Judge Evaluation."""

import typer
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.vectorstore.chroma import VectorStore
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, RerankedHybridRetriever
from vietnam_legal_rag.retrieval.graph import GraphEnhancedRetriever
from vietnam_legal_rag.graph.neo4j_client import Neo4jClient
from vietnam_legal_rag.generation.llm import build_default_llm
from vietnam_legal_rag.pipeline.rag import RAGPipeline
from vietnam_legal_rag.eval.e2e_evaluator import E2EEvaluator

app = typer.Typer()
console = Console()

@app.command()
def main(
    testset: str = typer.Option("data/eval/questions.v2.jsonl", "--testset"),
    samples: int = typer.Option(20, "--samples", "-n", help="Number of questions to evaluate"),
):
    testset_path = Path(testset)
    if not testset_path.exists():
        console.print(f"[red]Error: Testset not found at {testset_path}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold blue]⚖️ Vietnam Legal RAG — E2E LLM-as-a-Judge Evaluation[/bold blue]")
    
    settings = get_settings()
    console.print("Initializing Pipeline (Hybrid + Reranker + Graph)...")
    
    # Init Retrievers
    embedder = VietnameseEmbedder(model_name=settings.embedding_model, device="cpu")
    store = VectorStore()
    dense_retriever = DenseRetriever(embedder=embedder, store=store, top_k=50)
    bm25_retriever = BM25Retriever()
    bm25_retriever._load()
    
    hybrid = RerankedHybridRetriever(
        dense_retriever, bm25_retriever,
        dense_weight=0.5, bm25_weight=0.5,
        stage1_candidates=50,
        reranker_device="cpu"
    )
    
    neo4j_client = Neo4jClient()
    graph_retriever = GraphEnhancedRetriever(hybrid, neo4j_client)
    
    # Init LLM & Pipeline
    llm = build_default_llm()
    pipeline = RAGPipeline(retriever=graph_retriever, llm=llm)
    
    # Init Evaluator
    evaluator = E2EEvaluator(pipeline=pipeline, testset_path=testset_path)
    
    console.print(f"Running evaluation on {samples} samples...")
    results = evaluator.run(max_samples=samples)
    
    # Display Results
    console.print("\n[bold green]✅ Evaluation Complete![/bold green]")
    
    table = Table(title="End-to-End Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right", style="magenta")
    
    table.add_row("Faithfulness (Trung thực với Context)", f"{results['faithfulness_score']:.2%}")
    table.add_row("Answer Relevance (Trả lời đúng trọng tâm)", f"{results['relevance_score']:.2%}")
    table.add_row("Samples Evaluated", str(results['total_samples']))
    
    console.print(table)
    
    # Save detailed results
    out_path = Path("docs/e2e_evaluation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    console.print(f"Detailed logs saved to {out_path}")
    neo4j_client.close()

if __name__ == "__main__":
    app()
