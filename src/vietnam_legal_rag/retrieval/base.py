"""Common types for retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document


@dataclass
class RetrievalHit:
    """One retrieved chunk plus its score and source metadata."""

    document: Document
    score: float
    rank: int


__all__ = ["RetrievalHit"]
