"""Application settings loaded from environment variables and ``.env``.

Uses pydantic-settings so values are validated and typed at process start.
Each downstream module pulls the singleton via :func:`get_settings` rather
than re-reading the environment, which keeps tests easy to override.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level configuration for the RAG pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── LLM provider keys ──────────────────────────────────────────────────
    openai_api_key: str | None = Field(default=None)
    anthropic_api_key: str | None = Field(default=None)

    # ── LLM ────────────────────────────────────────────────────────────────
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=1024, gt=0)

    # ── Embeddings ─────────────────────────────────────────────────────────
    embedding_model: str = Field(default="keepitreal/vietnamese-sbert")
    embedding_device: str = Field(default="cpu")
    embedding_batch_size: int = Field(default=32, gt=0)

    # ── Vector store ───────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(default="data/index")
    chroma_collection_name: str = Field(default="vietnam_legal")

    # ── Chunking ───────────────────────────────────────────────────────────
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=64, ge=0)

    # ── Retrieval ──────────────────────────────────────────────────────────
    retrieval_k: int = Field(default=5, gt=0)
    retrieval_score_threshold: float = Field(default=0.0, ge=0.0)

    # ── Scraping ───────────────────────────────────────────────────────────
    scraper_user_agent: str = Field(
        default="Mozilla/5.0 (compatible; VietnamLegalRAG/0.1)"
    )
    scraper_request_timeout: int = Field(default=30, gt=0)
    scraper_rate_limit_seconds: float = Field(default=1.0, ge=0.0)
    scraper_base_url: str = Field(default="https://thuvienphapluat.vn")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a memoized :class:`Settings` instance.

    Cached so repeated calls are cheap and tests can override via
    ``get_settings.cache_clear()`` followed by monkey-patched env vars.
    """
    return Settings()


__all__ = ["Settings", "get_settings"]
