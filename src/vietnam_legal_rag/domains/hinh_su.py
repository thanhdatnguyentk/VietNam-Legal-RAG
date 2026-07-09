"""Bộ luật Hình sự — Penal Code domain."""

from __future__ import annotations

from vietnam_legal_rag.domains.base import DomainSpec

DOMAIN = DomainSpec(
    name="hinh_su",
    display_name="Bộ luật Hình sự 2015",
    description=(
        "Bộ luật Hình sự 2015 (Luật số 100/2015/QH13) và các luật sửa đổi, "
        "bổ sung — phạm vi các tội danh, khung hình phạt, các tình tiết "
        "tăng nặng / giảm nhẹ."
    ),
    source_urls=[
        # TODO: populate during scraping phase.
    ],
    keywords=[
        "tội phạm",
        "hình phạt",
        "tù",
        "cố ý",
        "vô ý",
        "đồng phạm",
        "tái phạm",
        "âm mưu",
    ],
)

__all__ = ["DOMAIN"]
