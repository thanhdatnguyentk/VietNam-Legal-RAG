"""Evaluation harness.

The evaluator runs the pipeline against the JSONL file in ``data/eval/``
and reports a small set of metrics: retrieval precision@k, retrieval
recall@k, and answer faithfulness. Full implementation is deferred to
the evaluation phase.
"""

from __future__ import annotations

__all__: list[str] = []
