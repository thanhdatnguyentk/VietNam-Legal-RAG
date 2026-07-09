"""Smoke tests: ensure the skeleton package is wired up correctly.

These tests do not exercise retrieval or generation (those modules are
intentional stubs at this stage). They just confirm that the public
imports, paths, and config behave the way the README and docs claim.
"""

from __future__ import annotations

import vietnam_legal_rag
from vietnam_legal_rag import config, paths
from vietnam_legal_rag.domains import DOMAIN_REGISTRY
from vietnam_legal_rag.generation.prompts import render_user_prompt
from vietnam_legal_rag.scrapers.base import RawDocument


def test_package_has_version() -> None:
    assert isinstance(vietnam_legal_rag.__version__, str)
    assert vietnam_legal_rag.__version__  # non-empty


def test_paths_resolve() -> None:
    assert paths.PROJECT_ROOT.is_dir()
    assert paths.DATA_DIR.is_dir()
    assert paths.RAW_DIR.is_dir()
    assert paths.PROCESSED_DIR.is_dir()
    assert paths.EVAL_DIR.is_dir()


def test_settings_load() -> None:
    settings = config.get_settings()
    # Defaults from the Settings model
    assert settings.chunk_size > 0
    assert settings.chunk_overlap >= 0
    assert settings.embedding_model
    assert settings.llm_model


def test_domain_registry_is_populated() -> None:
    assert len(DOMAIN_REGISTRY) >= 4
    assert "giao_thong" in DOMAIN_REGISTRY
    assert "dan_su" in DOMAIN_REGISTRY
    assert "hinh_su" in DOMAIN_REGISTRY
    assert "lao_dong" in DOMAIN_REGISTRY


def test_render_user_prompt_substitutes() -> None:
    out = render_user_prompt(context="ctx", question="q?")
    assert "ctx" in out
    assert "q?" in out
    assert "{context}" not in out
    assert "{question}" not in out


def test_raw_document_suggested_filename() -> None:
    doc = RawDocument(
        url="https://example.test/x",
        title="Luật Giao thông đường bộ",
        document_number="100/2019/NĐ-CP",
    )
    assert doc.suggested_filename() == "100_2019_NĐ-CP.txt"
