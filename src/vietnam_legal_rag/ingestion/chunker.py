"""Text chunker — split Vietnamese legal documents along structural boundaries.

Why structural chunking?
------------------------
Vietnamese legal documents follow a strict hierarchy:

    Chương (Chapter) → Điều (Article) → Khoản (Clause) → Điểm (Point)

The rule, the exception and the sanction clause usually all live inside a
single **Khoản**. A naive fixed-length splitter tears them apart so that
retrieval returns half-baked answers that the LLM cannot reconcile. The
correct strategy is to make each chunk a "semantically whole" unit:

* the **Điều** is the natural retrieval unit when it is short enough;
* when it overflows ``chunk_size``, we split along **Khoản** boundaries;
* if a single **Khoản** still overflows, we split along **Điểm**;
* anything that still overflows after all of the above falls back to
  :class:`langchain_text_splitters.RecursiveCharacterTextSplitter`, which
  only ever operates on the residual body — never across a Khoản boundary.

Public surface
--------------
* :class:`TextChunker` — interface;
* :class:`RecursiveVietnameseChunker` — default implementation;
* :func:`parse_articles` — diagnostic helper that returns the parsed
  (article_number, article_title, article_body) triples without chunking.

The chunker always adds a UUID ``chunk_id`` to every chunk's ``metadata``
plus a ``chunk_index`` (0-based, scoped to the source document) and
``split_level`` (``"article" | "clause" | "point" | "char"``).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from langchain_core.documents import Document

from vietnam_legal_rag.ingestion._regex import (
    ARTICLE_PATTERN,
    CLAUSE_PATTERN,
    POINT_PATTERN,
)


@dataclass(frozen=True)
class ParsedArticle:
    """One ``Điều`` extracted from a document."""

    number: str
    title: str
    body: str


def parse_articles(text: str) -> list[ParsedArticle]:
    """Return the list of ``Điều`` paragraphs found in ``text``.

    Header lines (everything before the first article) are dropped — they
    end up in the document-level metadata instead. If the document has no
    recognisable article headings, the function returns a single
    ``ParsedArticle`` so the rest of the pipeline keeps working.
    """
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        return [ParsedArticle(number="0", title="", body=text.strip())]
    articles: list[ParsedArticle] = []
    for i, m in enumerate(matches):
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():next_start].strip("\n")
        articles.append(ParsedArticle(number=m.group(1), title=m.group(2).strip(), body=body))
    return articles


# ────────────────────────────────────────────────────────────────────────────


class TextChunker(ABC):
    """Split a list of documents into a list of smaller documents."""

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        """Return new ``Document`` objects with potentially smaller ``page_content``."""


class RecursiveVietnameseChunker(TextChunker):
    """Three-level recursive splitter tuned for Vietnamese legal text."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be in [0, chunk_size)")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._char_splitter = _build_char_splitter(chunk_size, chunk_overlap)

    # ── Public API ─────────────────────────────────────────────────────────

    def split(self, documents: list[Document]) -> list[Document]:
        out: list[Document] = []
        for doc in documents:
            out.extend(self._split_one(doc))
        return out

    # ── Internals ──────────────────────────────────────────────────────────

    def _split_one(self, doc: Document) -> list[Document]:
        base_meta = dict(doc.metadata or {})
        for required_key in ("document_number", "document_title", "domain", "source_url"):
            base_meta.setdefault(required_key, "")
        text = doc.page_content
        articles = parse_articles(text)
        chunks: list[Document] = []
        for article in articles:
            chunks.extend(self._split_article(article, base_meta))
        # Annotate each chunk with chunk_index / total_chunks.
        total = len(chunks)
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = total
        return chunks

    def _split_article(self, article: ParsedArticle, base_meta: dict[str, str]) -> list[Document]:
        meta = {**base_meta, "article": article.number, "article_title": article.title}
        article_header = self._article_header(meta)
        # Fast path: the whole article fits in one chunk.
        if len(article.body) + len(article_header) + 1 <= self.chunk_size:
            body = f"{article_header}\n{article.body}".strip()
            return [self._make_chunk(body, meta, "article")]
        # Otherwise: split by Khoản.
        sub_chunks: list[Document] = []
        for cl_idx, (clause_no, clause_body) in enumerate(self._iter_clauses(article.body)):
            sub_meta = {**meta, "clause": str(clause_no), "point": ""}
            sub_header = self._clause_header(sub_meta)
            full_body = f"{article_header}\n{sub_header}{clause_body}".strip()
            if len(full_body) <= self.chunk_size:
                sub_chunks.append(self._make_chunk(full_body, sub_meta, "clause"))
                continue
            # Khoản too long: split by Điểm.
            clause_chunks = list(self._iter_points(clause_body))
            if not clause_chunks:
                # No point-level structure available. We *could* drop to the
                # character splitter, but that destroys the semantic boundary
                # of the Khoản. Prefer to emit one oversized chunk and let
                # downstream stages (the embedding model) handle it — the
                # alternative is silently breaking citations.
                sub_chunks.append(self._make_chunk(full_body, sub_meta, "clause"))
                continue
            for pt_idx, (point_letter, point_body) in enumerate(clause_chunks):
                pt_meta = {**sub_meta, "point": point_letter}
                pt_header = self._point_header(pt_meta)
                full_pt = f"{article_header}\n{sub_header}{pt_header}{point_body}".strip()
                if len(full_pt) <= self.chunk_size:
                    sub_chunks.append(self._make_chunk(full_pt, pt_meta, "point"))
                else:
                    # Điểm still overflows — char fallback is the only option.
                    for piece in self._char_splitter.split_text(full_pt):
                        sub_chunks.append(self._make_chunk(piece, pt_meta, "char"))
                _ = cl_idx, pt_idx  # silence linters until we use these for ordering
        return sub_chunks

    @staticmethod
    def _iter_clauses(body: str) -> Iterable[tuple[str, str]]:
        """Yield (clause_number, clause_body) pairs from a Điều body.

        Each clause body begins at the first non-whitespace character after
        the ``N.`` / ``N)`` marker, which preserves the leading capital
        (so "Đây" stays intact, not "ây").
        """
        matches = list(CLAUSE_PATTERN.finditer(body))
        if not matches:
            yield "1", body.strip()
            return
        # Leading text before the first numbered clause (the article's
        # intro paragraph) becomes clause "0".
        first_start = matches[0].start()
        if first_start > 0 and body[:first_start].strip():
            yield "0", body[:first_start].strip()
        for i, m in enumerate(matches):
            next_start = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            clause_no = m.group(1)
            # ``m.start(2)`` is the position of the first non-whitespace
            # character after the delimiter — this preserves the leading
            # letter (so "Đây" stays intact, not "ây").
            clause_body = body[m.start(2):next_start].strip("\n")
            yield clause_no, clause_body

    @staticmethod
    def _iter_points(body: str) -> list[tuple[str, str]]:
        """Yield (point_letter, point_body) pairs from a Khoản body."""
        matches = list(POINT_PATTERN.finditer(body))
        results: list[tuple[str, str]] = []
        if not matches:
            return results
        for i, m in enumerate(matches):
            next_start = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            # ``m.start(2)`` is the first non-whitespace char after ``)``.
            results.append((m.group(1), body[m.start(2):next_start].strip("\n")))
        return results

    @staticmethod
    def _article_header(meta: dict[str, str]) -> str:
        """Build the document-level header line emitted before every article."""
        parts: list[str] = []
        if meta.get("document_number"):
            parts.append(meta["document_number"])
        if meta.get("article_title"):
            parts.append(f"Điều {meta['article']} — {meta['article_title']}")
        else:
            parts.append(f"Điều {meta['article']}")
        return " | ".join(parts)

    @staticmethod
    def _clause_header(meta: dict[str, str]) -> str:
        """Build a per-clause indicator like ``\nKhoản 3\n`` (no part duplication)."""
        return f"\nKhoản {meta['clause']}\n" if meta.get("clause") else "\n"

    @staticmethod
    def _point_header(meta: dict[str, str]) -> str:
        """Build a per-point indicator like ``\nĐiểm a —\n``."""
        if not meta.get("point"):
            return ""
        return f"\nĐiểm {meta['point']} —\n"

    @staticmethod
    def _make_chunk(text: str, meta: dict[str, str], split_level: str) -> Document:
        full_meta = {**meta, "chunk_id": uuid.uuid4().hex, "split_level": split_level}
        return Document(page_content=text, metadata=full_meta)


# ────────────────────────────────────────────────────────────────────────────


def _build_char_splitter(chunk_size: int, chunk_overlap: int):
    """Lazy import — the splitter is only constructed when actually used."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:  # pragma: no cover - we document the dep in pyproject
        raise ImportError(
            "langchain-text-splitters is required by RecursiveVietnameseChunker. "
            "Install it with: pip install langchain-text-splitters"
        )
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )


__all__ = [
    "ParsedArticle",
    "parse_articles",
    "TextChunker",
    "RecursiveVietnameseChunker",
]
