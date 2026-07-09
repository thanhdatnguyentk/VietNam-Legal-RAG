"""CLI: run the evaluation harness against ``data/eval/``.

Usage
-----

    python scripts/eval.py
    python scripts/eval.py --k 10
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from vietnam_legal_rag.config import get_settings
from vietnam_legal_rag.eval.evaluator import EvalReport
from vietnam_legal_rag.paths import EVAL_DIR

app = typer.Typer(add_completion=False, help="Run the evaluation harness.")
console = Console()


@app.command()
def main(
    eval_dir: Path = typer.Option(EVAL_DIR, "--eval-dir"),
    k: int = typer.Option(5, "--k", help="Compute precision@k / recall@k with this k."),
) -> None:
    """Evaluate the pipeline against the JSONL eval set."""
    settings = get_settings()
    _ = settings
    console.print(f"[bold]Vietnam Legal RAG — eval[/bold]")
    console.print(f"Eval dir: {eval_dir}")
    console.print(f"k:        {k}")
    # SKELETON — the evaluator is not implemented yet.
    raise NotImplementedError("eval.py is a skeleton — see docs/roadmap.md.")


__all__: list[str] = []  # re-export guard


if __name__ == "__main__":
    try:
        app()
    except NotImplementedError as exc:  # pragma: no cover - dev affordance
        console.print(f"[red]TODO:[/red] {exc}")
        sys.exit(2)
