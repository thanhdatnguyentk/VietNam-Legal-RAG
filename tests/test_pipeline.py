"""Pipeline tests — stubs to be expanded in the pipeline phase."""

from __future__ import annotations

import pytest

from vietnam_legal_rag.generation.prompts import SYSTEM_PROMPT
from vietnam_legal_rag.pipeline.rag import RAGAnswer, RAGPipeline


def test_system_prompt_in_vietnamese() -> None:
    assert "trợ lý" in SYSTEM_PROMPT.lower()
    assert "ngữ cảnh" in SYSTEM_PROMPT.lower()


def test_rag_answer_dataclass_defaults() -> None:
    ans = RAGAnswer(question="q", answer="a")
    assert ans.citations == []
    assert tuple(ans.hits) == ()


def test_rag_pipeline_query_is_stub() -> None:
    pipeline = RAGPipeline.__new__(RAGPipeline)  # skip LLM init
    with pytest.raises(NotImplementedError):
        pipeline.query("anything")
