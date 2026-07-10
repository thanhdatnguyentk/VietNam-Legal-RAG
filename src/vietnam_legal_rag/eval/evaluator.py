"""Evaluator interface and basic retrieval evaluation."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vietnam_legal_rag.retrieval.hybrid import HybridRetriever

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

class BaselineRetrieverEvaluator(Evaluator):
    """Evaluates the retriever (Dense or Hybrid) using a JSONL test set."""

    def __init__(self, retriever: Any, testset_path: Path, top_k: int = 5):
        self.retriever = retriever
        self.testset_path = testset_path
        self.top_k = top_k

    def run(self) -> EvalReport:
        if not self.testset_path.exists():
            raise FileNotFoundError(f"Testset not found: {self.testset_path}")

        total = 0
        hits_count = 0  # number of queries where the true doc was found

        with open(self.testset_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                question = record["question"]
                true_doc_id = record["ground_truth_document_number"]

                # Retrieve candidates
                hits = self.retriever.retrieve(question, top_k=self.top_k)
                total += 1
                
                # Check if ground truth document is in the top-k results
                found = False
                if hits:
                    for hit in hits:
                        doc_num = hit.document.metadata.get("document_number", "")
                        if true_doc_id in doc_num:
                            found = True
                            break
                    
                    if found:
                        hits_count += 1
                    
        precision_at_k = hits_count / total if total > 0 else 0.0
        recall_at_k = hits_count / total if total > 0 else 0.0
        
        return EvalReport(
            total=total,
            retrieval_precision_at_k=precision_at_k,
            retrieval_recall_at_k=recall_at_k
        )

__all__ = ["EvalReport", "Evaluator", "BaselineRetrieverEvaluator"]
