"""LLM client — provider-agnostic interface for the generation step."""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.messages import SystemMessage, HumanMessage

from vietnam_legal_rag.config import get_settings


class LLMClient(ABC):
    """Abstract LLM client used by :class:`RAGPipeline`."""

    @abstractmethod
    def generate(self, system: str, user: str, *, max_tokens: int | None = None) -> str:
        """Return a single completion for the given prompt."""


class LangchainLLMClient(LLMClient):
    """LLM client wrapping LangChain Chat Models."""

    def __init__(self, model: "BaseChatModel"):
        self.model = model

    def generate(self, system: str, user: str, *, max_tokens: int | None = None) -> str:
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user)
        ]
        
        # If the underlying model supports max_tokens at call time, we can pass it,
        # but for simplicity we rely on the init config unless explicitly overridden.
        # ChatOpenAI and ChatAnthropic handle kwargs differently, so we stick to invoke().
        response = self.model.invoke(messages)
        
        # Extract the content text
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # E.g., for Claude returning a list of text blocks
            return "".join([c["text"] for c in content if c["type"] == "text"])
        
        return str(content)


def build_default_llm() -> LLMClient:
    """Construct the default LLM client from :func:`get_settings`."""
    settings = get_settings()
    
    if settings.llm_provider.lower() == "openai":
        try:
            from langchain_openai import ChatOpenAI
            chat_model = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key if settings.openai_api_key else None
            )
            return LangchainLLMClient(chat_model)
        except ImportError:
            raise ImportError("langchain-openai is not installed. Run `pip install langchain-openai`")
            
    elif settings.llm_provider.lower() == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            chat_model = ChatAnthropic(
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.anthropic_api_key if settings.anthropic_api_key else None
            )
            return LangchainLLMClient(chat_model)
        except ImportError:
            raise ImportError("langchain-anthropic is not installed. Run `pip install langchain-anthropic`")
            
    elif settings.llm_provider.lower() == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            chat_model = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                google_api_key=settings.gemini_api_key if settings.gemini_api_key else None
            )
            return LangchainLLMClient(chat_model)
        except ImportError:
            raise ImportError("langchain-google-genai is not installed. Run `pip install langchain-google-genai`")
            
    elif settings.llm_provider.lower() == "ollama":
        try:
            from langchain_ollama import ChatOllama
            chat_model = ChatOllama(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                base_url="http://localhost:11434"
            )
            return LangchainLLMClient(chat_model)
        except ImportError:
            raise ImportError("langchain-ollama is not installed. Run `pip install langchain-ollama`")
            
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


__all__ = ["LLMClient", "LangchainLLMClient", "build_default_llm"]
