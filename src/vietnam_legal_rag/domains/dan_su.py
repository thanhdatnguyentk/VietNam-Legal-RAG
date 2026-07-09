"""Bộ luật Dân sự — Civil Code domain."""

from __future__ import annotations

from vietnam_legal_rag.domains.base import DomainSpec

DOMAIN = DomainSpec(
    name="dan_su",
    display_name="Bộ luật Dân sự 2015",
    description=(
        "Bộ luật Dân sự 2015 (Luật số 91/2015/QH13) và các luật chuyên ngành "
        "liên quan đến hợp đồng, nghĩa vụ dân sự, quyền sở hữu và thừa kế."
    ),
    source_urls=[
        # TODO: populate during scraping phase.
    ],
    keywords=[
        "hợp đồng",
        "nghĩa vụ dân sự",
        "quyền sở hữu",
        "thừa kế",
        "bồi thường thiệt hại",
        "giao dịch dân sự",
    ],
)

__all__ = ["DOMAIN"]
