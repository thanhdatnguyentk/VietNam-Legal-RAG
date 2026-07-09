"""High-level RAG pipeline that ties retrieval and generation together."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.documents import Document

from vietnam_legal_rag.generation.llm import LLMClient
from vietnam_legal_rag.generation.prompts import SYSTEM_PROMPT, render_user_prompt
from vietnam_legal_rag.retrieval.base import RetrievalHit


@dataclass
class RAGAnswer:
    """The final answer plus the chunks that grounded it."""

    question: str
    answer: str
    citations: list[str] = field(default_factory=list)
    hits: Sequence[RetrievalHit] = field(default_factory=tuple)


class RAGPipeline:
    """Wire a retriever and an LLM into a single ``query()`` entry point."""

    def __init__(self, retriever, llm: LLMClient) -> None:
        self.retriever = retriever
        self.llm = llm

    def _format_context(self, hits: Sequence[RetrievalHit]) -> str:
        """Stitch the retrieved chunks into a single context string."""
        parts: list[str] = []
        for i, hit in enumerate(hits, start=1):
            meta = hit.document.metadata or {}
            header = (
                f"[{i}] "
                f"{meta.get('document_number', '?')} — "
                f"Điều {meta.get('article', '?')}, "
                f"Khoản {meta.get('clause', '?')}"
            )
            parts.append(f"{header}\n{hit.document.page_content.strip()}")
        return "\n\n".join(parts)

    def query(self, question: str) -> RAGAnswer:  # pragma: no cover - skeleton
        """Run a full RAG query and return the structured :class:`RAGAnswer`."""
        raise NotImplementedError("RAGPipeline.query is a skeleton.")


__all__ = ["RAGAnswer", "RAGPipeline", "Document"]
