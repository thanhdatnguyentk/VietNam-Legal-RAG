"""Base types for legal-domain specifications."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainSpec:
    """Static description of one area of Vietnamese law.

    Attributes:
        name: Short snake_case identifier used in CLI and filesystem
            (``giao_thong``, ``dan_su``, …).
        display_name: Human-readable Vietnamese label.
        description: One-paragraph explanation of the scope.
        source_urls: Starting URLs used by the scraper. Can be either
            document detail pages or category listings.
        keywords: Seed keywords used by the Router Agent in later phases
            to triage inbound queries to the right domain.
    """

    name: str
    display_name: str
    description: str
    source_urls: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


__all__ = ["DomainSpec"]
