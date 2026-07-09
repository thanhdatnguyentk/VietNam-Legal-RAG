"""Ingestion pipeline: load raw documents → chunk → write processed JSONL.

The pipeline is split into three small interfaces so each stage can be
swapped or benchmarked in isolation:

* :class:`DocumentLoader` — read ``data/raw/*`` into a stream of
  ``langchain_core.documents.Document`` objects.
* :class:`TextChunker` — split each document into smaller chunks while
  preserving Vietnamese legal structure (Điều → Khoản → Điểm).
* :func:`run_ingestion` — orchestrate the two and persist the result.
"""

from __future__ import annotations

__all__: list[str] = []
