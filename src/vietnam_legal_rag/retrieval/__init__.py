"""Retrieval strategies.

* :class:`DenseRetriever` — pure embedding cosine similarity (the workhorse
  for Vietnamese semantic search).
* :class:`HybridRetriever` — BM25 + dense, intended for a later phase.
"""

from __future__ import annotations

__all__: list[str] = []
