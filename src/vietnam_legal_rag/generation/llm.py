"""LLM client — provider-agnostic interface for the generation step."""

from __future__ import annotations

from abc import ABC, abstractmethod

from vietnam_legal_rag.config import get_settings


class LLMClient(ABC):
    """Abstract LLM client used by :class:`RAGPipeline`."""

    @abstractmethod
    def generate(self, system: str, user: str, *, max_tokens: int | None = None) -> str:
        """Return a single completion for the given prompt."""


def build_default_llm() -> LLMClient:  # pragma: no cover - skeleton
    """Construct the default LLM client from :func:`get_settings`.

    TODO: branch on ``settings.llm_provider`` and instantiate either
    ``langchain_openai.ChatOpenAI`` or ``langchain_anthropic.ChatAnthropic``.
    """
    settings = get_settings()
    _ = settings
    raise NotImplementedError("build_default_llm is a skeleton.")


__all__ = ["LLMClient", "build_default_llm"]
