"""Evaluator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EvalReport:
    """Aggregate metrics for one evaluation run."""

    total: int
    retrieval_precision_at_k: float
    retrieval_recall_at_k: float
    answer_faithfulness: float | None = None  # None when not measured


class Evaluator(ABC):
    """Compute :class:`EvalReport` from a pipeline + eval set."""

    @abstractmethod
    def run(self) -> EvalReport: ...


__all__ = ["EvalReport", "Evaluator"]
