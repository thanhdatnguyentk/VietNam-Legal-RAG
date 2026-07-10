"""Error Analysis — identify patterns in retrieval failures.

Runs retrieval on the full testset and reports which questions failed,
grouped by domain, to help diagnose systematic weaknesses.
"""

import json
import typer
from pathlib import Path
from collections import Counter, defaultdict
from rich.console import Console
from rich.table import Table

from vietnam_legal_rag.eval.evaluator import BaselineRetrieverEvaluator
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.retrieval.dense import DenseRetriever
from vietnam_legal_rag.retrieval.hybrid import BM25Retriever, HybridRetriever
from vietnam_legal_rag.vectorstore.chroma import VectorStore
from vietnam_legal_rag.config import get_settings

app = typer.Typer()
console = Console()


@app.command()
def main(
    testset: str = typer.Option("data/eval/questions.v2.jsonl", "--testset"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    mode: str = typer.Option("bm25", "--mode", "-m", help="dense|bm25|hybrid"),
    output: str = typer.Option("docs/error_analysis.md", "--output", "-o"),
) -> None:
    testset_path = Path(testset)
    console.print("[bold blue]🔬 Error Analysis — VietLegal RAG[/bold blue]")
    
    # Initialize retriever
    settings = get_settings()
    
    if mode in ("dense", "hybrid"):
        embedder = VietnameseEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)
        store = VectorStore()
        dense_retriever = DenseRetriever(embedder=embedder, store=store, top_k=top_k)
    
    if mode in ("bm25", "hybrid"):
        bm25_retriever = BM25Retriever()
        bm25_retriever._load()
    
    if mode == "dense":
        retriever = dense_retriever
    elif mode == "bm25":
        retriever = bm25_retriever
    else:
        retriever = HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.5, bm25_weight=0.5)
    
    # Run retrieval on each question
    console.print(f"Running {mode} retrieval on {testset_path}...")
    
    successes = []
    failures = []
    domain_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    
    with open(testset_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    
    for i, record in enumerate(records):
        question = record["question"]
        true_doc_id = record["ground_truth_document_number"]
        
        hits = retriever.retrieve(question, top_k=top_k)
        
        found = False
        retrieved_docs = []
        for hit in hits:
            doc_num = hit.document.metadata.get("document_number", "")
            retrieved_docs.append(doc_num)
            if true_doc_id in doc_num:
                found = True
        
        # Infer domain from testset metadata or from ground truth doc path
        domain = record.get("metadata", {}).get("domain", "unknown") if "metadata" in record else "unknown"
        if domain == "unknown":
            # Try to infer from ground truth
            for d in ["giao_thong", "dat_dai", "lao_dong", "y_te", "thue", "dan_su", 
                       "doanh_nghiep", "hanh_chinh", "hinh_su", "moi_truong", "giao_duc", "khac"]:
                # Check if there's a processed file
                check_path = Path(f"data/processed/{d}")
                if check_path.exists():
                    for jsonl_f in check_path.glob("*.jsonl"):
                        if true_doc_id.replace("/", "_") in jsonl_f.name:
                            domain = d
                            break
                if domain != "unknown":
                    break
        
        domain_stats[domain]["total"] += 1
        
        entry = {
            "idx": i + 1,
            "question": question[:80],
            "ground_truth": true_doc_id,
            "retrieved": retrieved_docs[:3],
            "domain": domain,
        }
        
        if found:
            successes.append(entry)
            domain_stats[domain]["correct"] += 1
        else:
            failures.append(entry)
    
    total = len(records)
    n_correct = len(successes)
    n_failed = len(failures)
    
    # === Print Summary Table ===
    summary_table = Table(title=f"Error Analysis Summary ({mode}, Top-{top_k})")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right", style="green")
    summary_table.add_row("Total queries", str(total))
    summary_table.add_row("Correct", str(n_correct))
    summary_table.add_row("Failed", str(n_failed))
    summary_table.add_row("Recall", f"{n_correct / total:.2%}")
    console.print(summary_table)
    
    # === Domain breakdown ===
    domain_table = Table(title="Recall by Domain")
    domain_table.add_column("Domain", style="cyan")
    domain_table.add_column("Total", justify="right")
    domain_table.add_column("Correct", justify="right", style="green")
    domain_table.add_column("Recall", justify="right", style="magenta")
    
    for domain in sorted(domain_stats.keys()):
        stats = domain_stats[domain]
        recall = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        domain_table.add_row(domain, str(stats["total"]), str(stats["correct"]), f"{recall:.0%}")
    
    console.print(domain_table)
    
    # === Failure examples ===
    if failures:
        fail_table = Table(title=f"First 20 Failures")
        fail_table.add_column("#", justify="right", style="dim")
        fail_table.add_column("Ground Truth", style="red")
        fail_table.add_column("Retrieved Top-3", style="yellow")
        fail_table.add_column("Question (truncated)", style="white")
        
        for entry in failures[:20]:
            fail_table.add_row(
                str(entry["idx"]),
                entry["ground_truth"],
                ", ".join(entry["retrieved"]),
                entry["question"],
            )
        console.print(fail_table)
    
    # === Save detailed report ===
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Error Analysis Report ({mode}, Top-{top_k})\n\n")
        f.write(f"**Date**: 2026-07-10 | **Testset**: {testset_path} ({total} queries)\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total | {total} |\n")
        f.write(f"| Correct | {n_correct} |\n")
        f.write(f"| Failed | {n_failed} |\n")
        f.write(f"| Recall@{top_k} | {n_correct / total:.2%} |\n\n")
        
        f.write(f"## Recall by Domain\n\n")
        f.write(f"| Domain | Total | Correct | Recall |\n|---|---|---|---|\n")
        for domain in sorted(domain_stats.keys()):
            stats = domain_stats[domain]
            recall = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            f.write(f"| {domain} | {stats['total']} | {stats['correct']} | {recall:.0%} |\n")
        
        f.write(f"\n## Failed Queries ({n_failed})\n\n")
        for entry in failures:
            f.write(f"- **#{entry['idx']}** `{entry['ground_truth']}` → Retrieved: `{', '.join(entry['retrieved'])}` — _{entry['question']}_\n")
    
    console.print(f"\n[bold green]✅ Detailed report saved to {output_path}[/bold green]")


if __name__ == "__main__":
    app()
