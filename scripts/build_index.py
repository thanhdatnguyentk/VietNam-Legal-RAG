"""CLI: build the ChromaDB index from processed chunks.

Usage
-----

    python scripts/build_index.py
    python scripts/build_index.py --processed-dir data/processed --reset
    python scripts/build_index.py --embedding-model BAAI/bge-m3 --device cuda
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.embeddings.vietnamese import VietnameseEmbedder
from vietnam_legal_rag.paths import PROCESSED_DIR
from vietnam_legal_rag.vectorstore.chroma import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Build / refresh the vector index.")
console = Console()


def load_chunks(processed_dir: Path) -> list[dict]:
    """Load all chunks from JSONL files in the processed directory."""
    chunks = []
    for jsonl_file in sorted(processed_dir.rglob("*.jsonl")):
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                chunks.append(rec)
    return chunks


@app.command()
def main(
    processed_dir: Path = typer.Option(PROCESSED_DIR, "--processed-dir"),
    reset: bool = typer.Option(False, "--reset", help="Drop the existing collection first."),
    embedding_model: str = typer.Option(None, "--embedding-model", help="Override embedding model."),
    device: str = typer.Option(None, "--device", help="Override device (cpu/cuda/auto)."),
    batch_size: int = typer.Option(64, "--batch-size", help="Embedding batch size."),
    index_dir: str = typer.Option(None, "--index-dir", help="Override ChromaDB persist dir."),
) -> None:
    """Embed processed chunks and upsert them into ChromaDB."""
    settings = get_settings()

    model_name = embedding_model or settings.embedding_model
    dev = device or settings.embedding_device
    persist_dir = index_dir or settings.chroma_persist_dir

    console.print("[bold]🏛️ Vietnam Legal RAG — Build Index[/bold]")
    console.print(f"Embedding:        {model_name} ({dev})")
    console.print(f"Batch size:       {batch_size}")
    console.print(f"Chroma persist:   {persist_dir}")
    console.print(f"Collection:       {settings.chroma_collection_name}")
    console.print(f"Processed dir:    {processed_dir}")
    console.print(f"Reset:            {reset}")
    console.print()

    # Step 1: Load all chunks
    console.print("[blue]Loading chunks...[/blue]")
    chunks = load_chunks(processed_dir)
    console.print(f"  Loaded {len(chunks):,} raw chunks from {processed_dir}")

    # Deduplicate chunks by ID
    unique_chunks = {}
    for i, c in enumerate(chunks):
        cid = c.get("metadata", {}).get("chunk_id", f"chunk_{i}")
        if cid not in unique_chunks:
            unique_chunks[cid] = c
    
    chunks = list(unique_chunks.values())
    console.print(f"  After deduplication: {len(chunks):,} unique chunks")

    if not chunks:
        console.print("[red]No chunks found. Run ingestion first.[/red]")
        sys.exit(1)

    # Step 2: Initialize embedder
    console.print(f"\n[blue]Initializing embedder ({model_name})...[/blue]")
    embedder = VietnameseEmbedder(model_name=model_name, device=dev)
    embedder._load()  # Force load to show progress and catch errors early
    console.print(f"  Embedding dimension: {embedder.dimension}")

    # Step 3: Initialize vector store
    console.print(f"\n[blue]Initializing ChromaDB ({persist_dir})...[/blue]")
    store = VectorStore(persist_dir=persist_dir)

    if reset:
        store.reset()
        console.print("  [yellow]Collection reset[/yellow]")
    else:
        existing = store.count()
        console.print(f"  Existing vectors: {existing:,}")

    # Step 4: Embed and index in batches
    console.print(f"\n[blue]Embedding & indexing {len(chunks):,} chunks...[/blue]")
    start_time = time.time()

    total_embedded = 0
    embed_batch_size = batch_size

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding...", total=len(chunks))

        for i in range(0, len(chunks), embed_batch_size):
            batch = chunks[i:i + embed_batch_size]

            # Prepare batch data
            texts = [c["text"] for c in batch]
            ids = [c["metadata"].get("chunk_id", f"chunk_{i+j}") for j, c in enumerate(batch)]
            metadatas = [c.get("metadata", {}) for c in batch]

            # Embed the batch
            embeddings = embedder.embed_documents(texts)

            # Upsert into ChromaDB
            store.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            total_embedded += len(batch)
            progress.update(
                task,
                advance=len(batch),
                description=f"[green]Batch {i // embed_batch_size + 1}[/green]",
            )

    elapsed = time.time() - start_time

    # Step 5: Summary
    console.print(f"\n[bold green]{'='*50}[/bold green]")
    console.print(f"[bold]Indexing Complete![/bold]")
    console.print(f"  Chunks embedded:  {total_embedded:,}")
    console.print(f"  Index size:       {store.count():,} vectors")
    console.print(f"  Time:             {elapsed:.1f}s")
    console.print(f"  Speed:            {total_embedded / elapsed:.1f} chunks/s")
    console.print(f"  Index path:       {persist_dir}")

    # Test query
    console.print(f"\n[blue]Testing retrieval...[/blue]")
    test_query = "mức phạt vượt đèn đỏ xe ô tô"
    query_emb = embedder.embed_query(test_query)
    results = store.query(query_emb, top_k=3)
    console.print(f"  Query: \"{test_query}\"")
    for i, r in enumerate(results, 1):
        score = 1.0 - r["distance"]
        meta = r["metadata"]
        doc_num = meta.get("document_number", "?")
        article = meta.get("article", "?")
        clause = meta.get("clause", "?")
        console.print(
            f"  #{i} | Score: {score:.3f} | {doc_num} Điều {article} K{clause} | "
            f"{r['document'][:80]}..."
        )


if __name__ == "__main__":
    app()
