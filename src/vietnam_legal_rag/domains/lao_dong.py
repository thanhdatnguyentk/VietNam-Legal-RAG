"""Bộ luật Lao động — Labor Code domain."""

from __future__ import annotations

from vietnam_legal_rag.domains.base import DomainSpec

DOMAIN = DomainSpec(
    name="lao_dong",
    display_name="Bộ luật Lao động 2019",
    description=(
        "Bộ luật Lao động 2019 (Luật số 45/2019/QH14) và các Nghị định "
        "hướng dẫn — hợp đồng lao động, sa thải, bảo hiểm xã hội, "
        "thời giờ làm việc và nghỉ phép."
    ),
    source_urls=[
        # TODO: populate during scraping phase.
    ],
    keywords=[
        "hợp đồng lao động",
        "sa thải",
        "lương",
        "bảo hiểm xã hội",
        "nghỉ phép",
        "thời giờ làm việc",
        "thử việc",
    ],
)

__all__ = ["DOMAIN"]
