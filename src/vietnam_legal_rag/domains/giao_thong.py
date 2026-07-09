"""Luật Giao thông đường bộ — Road Traffic Law domain."""

from __future__ import annotations

from vietnam_legal_rag.domains.base import DomainSpec

DOMAIN = DomainSpec(
    name="giao_thong",
    display_name="Luật Giao thông đường bộ",
    description=(
        "Luật Giao thông đường bộ 2008 (Luật số 23/2008/QH12) cùng các văn bản "
        "sửa đổi, bổ sung và các Nghị định hướng dẫn — đặc biệt Nghị định "
        "100/2019/NĐ-CP và Nghị định 168/2024/NĐ-CP về xử phạt vi phạm hành "
        "chính trong lĩnh vực giao thông."
    ),
    source_urls=[
        # TODO: populate with real thuvienphapluat.vn URLs during scraping phase.
    ],
    keywords=[
        "giao thông",
        "lái xe",
        "GPLX",
        "Giấy phép lái xe",
        "vi phạm giao thông",
        "nồng độ cồn",
        "tốc độ",
        "vượt đèn đỏ",
    ],
)

__all__ = ["DOMAIN"]
