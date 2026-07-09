"""Legal-domain registry.

Each domain (traffic law, civil code, criminal code, …) is described by a
:class:`DomainSpec`. The registry exposed as :data:`DOMAIN_REGISTRY` maps
short domain names to their specs and is used by scripts to drive scraping
and ingestion.
"""

from __future__ import annotations

from vietnam_legal_rag.domains.base import DomainSpec
from vietnam_legal_rag.domains.dan_su import DOMAIN as DAN_SU
from vietnam_legal_rag.domains.giao_thong import DOMAIN as GIAO_THONG
from vietnam_legal_rag.domains.hinh_su import DOMAIN as HINH_SU
from vietnam_legal_rag.domains.lao_dong import DOMAIN as LAO_DONG

DOMAIN_REGISTRY: dict[str, DomainSpec] = {
    spec.name: spec
    for spec in (GIAO_THONG, DAN_SU, HINH_SU, LAO_DONG)
}

__all__ = ["DomainSpec", "DOMAIN_REGISTRY"]
