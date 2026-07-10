"""Title enrichment for legal document chunks.

Vietnamese legal text at the Khoản/Điểm level often uses generic language
that fails vector similarity search.  Title enrichment **prepends the full
hierarchical title chain** to each chunk so that embeddings capture the
broader legal context.

Example:
    Before:  "Phạt tiền từ 2.000.000 đồng..."
    After:   "[NĐ 100/2019/NĐ-CP] → [Chương II] → [Mục 1] → [Điều 5] Khoản 1, Điểm a:
              Phạt tiền từ 2.000.000 đồng..."

The enrichment is already integrated into
:class:`~vietnam_legal_rag.ingestion.chunker.StructuralVietnameseChunker`
via its ``enrich_title=True`` flag.  This module provides standalone
utility functions for cases where you need to enrich chunks from other
sources.
"""

from __future__ import annotations

from langchain_core.documents import Document


def build_title_chain(metadata: dict) -> str:
    """Build a hierarchical title string from chunk metadata.

    Parameters
    ----------
    metadata:
        Must contain some of: ``title``, ``chapter``, ``section``,
        ``article``, ``article_title``, ``clause``, ``point``.

    Returns
    -------
    str
        A string like ``[Luật X] → [Chương II] → [Điều 5. Tên điều]``.
    """
    parts: list[str] = []

    doc_title = metadata.get("title", "") or metadata.get("document_title", "")
    if doc_title:
        parts.append(f"[{doc_title}]")

    chapter = metadata.get("chapter", "")
    if chapter:
        parts.append(f"[{chapter}]")

    section = metadata.get("section", "")
    if section:
        parts.append(f"[{section}]")

    article = metadata.get("article", "")
    article_title = metadata.get("article_title", "")
    if article:
        art_str = f"Điều {article}"
        if article_title:
            art_str += f". {article_title}"
        parts.append(f"[{art_str}]")

    return " → ".join(parts)


def enrich_chunk(chunk: Document) -> Document:
    """Prepend the hierarchical title chain to a chunk's content.

    Modifies the chunk **in place** and returns it for convenience.
    If the chunk already has a ``title_chain`` in its metadata, this
    function is a no-op.
    """
    if chunk.metadata.get("title_chain"):
        return chunk

    title_chain = build_title_chain(chunk.metadata)
    if title_chain:
        chunk.metadata["title_chain"] = title_chain
        chunk.page_content = f"{title_chain}\n{chunk.page_content}"

    return chunk


def enrich_chunks(chunks: list[Document]) -> list[Document]:
    """Enrich a list of chunks with title chains."""
    return [enrich_chunk(c) for c in chunks]


__all__ = ["build_title_chain", "enrich_chunk", "enrich_chunks"]
