"""Text chunker — split documents into retrieval-friendly pieces.

The SOTA choice for Vietnamese legal text is **structural chunking**: respect
the natural Điều / Khoản / Điểm hierarchy so that a chunk never contains a
half article. A fixed-size splitter is *not* appropriate here because it
will tear apart the rule, the exception, and the sanction clause that
typically sit within a single Khoản.

This module provides:

* :class:`TextChunker` — abstract interface.
* :class:`RecursiveVietnameseChunker` — fallback using LangChain splitter.
* :class:`StructuralVietnameseChunker` — **SOTA** regex-based parser that
  respects the Điều → Khoản → Điểm hierarchy of Vietnamese law.
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# ── Regex patterns for Vietnamese legal document structure ────────────────

# Each pattern matches the START of a structural element on its own line.
_RE_PHAN = re.compile(r"^Phần\s+(thứ\s+)?\w+", re.MULTILINE | re.IGNORECASE)
_RE_CHUONG = re.compile(r"^Chương\s+[IVXLCDM\d]+", re.MULTILINE)
_RE_MUC = re.compile(r"^Mục\s+\d+", re.MULTILINE)
_RE_DIEU = re.compile(r"^Điều\s+(\d+)[\.\:]?\s*(.*)", re.MULTILINE)
_RE_KHOAN = re.compile(r"^(\d+)\.\s+(.*)", re.MULTILINE)
_RE_DIEM = re.compile(r"^([a-zđ])\)\s+(.*)", re.MULTILINE)


@dataclass
class _StructuralContext:
    """Track the current position in the document hierarchy."""

    document_title: str = ""
    document_number: str = ""
    phan: str = ""
    chuong: str = ""
    muc: str = ""
    dieu: str = ""
    dieu_title: str = ""
    khoan: str = ""
    diem: str = ""

    def title_chain(self) -> str:
        """Build a hierarchical title string for enrichment."""
        parts: list[str] = []
        if self.document_title:
            parts.append(f"[{self.document_title}]")
        if self.chuong:
            parts.append(f"[{self.chuong}]")
        if self.muc:
            parts.append(f"[{self.muc}]")
        dieu_str = f"Điều {self.dieu}"
        if self.dieu_title:
            dieu_str += f". {self.dieu_title}"
        if self.dieu:
            parts.append(f"[{dieu_str}]")
        return " → ".join(parts)


class TextChunker(ABC):
    """Split a list of documents into a list of smaller documents."""

    @abstractmethod
    def split(self, documents: list[Document]) -> list[Document]:
        """Return new ``Document`` objects with potentially smaller ``page_content``."""


class RecursiveVietnameseChunker(TextChunker):
    """Split using ``RecursiveCharacterTextSplitter`` tuned for Vietnamese law.

    This is a **fallback** for documents that don't follow standard legal
    structure. Prefer :class:`StructuralVietnameseChunker` whenever possible.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: list[Document]) -> list[Document]:
        """Split using RecursiveCharacterTextSplitter with VN-aware separators."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            separators=["\nĐiều ", "\nKhoản ", "\nĐiểm ", "\n\n", "\n", " "],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        return splitter.split_documents(documents)


class StructuralVietnameseChunker(TextChunker):
    """Parse Vietnamese legal text by its natural Điều → Khoản → Điểm hierarchy.

    Each chunk represents the smallest legal unit (typically a Khoản or the
    entire Điều if it has no numbered clauses). Metadata on each chunk
    includes: ``article``, ``article_title``, ``clause``, ``point``,
    ``title_chain``, and ``chunk_id``.

    The ``title_chain`` field contains the full hierarchical path prepended
    to the chunk content for improved embedding quality (Title Enrichment).
    """

    def __init__(self, *, enrich_title: bool = True) -> None:
        self.enrich_title = enrich_title

    def split(self, documents: list[Document]) -> list[Document]:
        """Split all documents using structural parsing."""
        all_chunks: list[Document] = []
        for doc in documents:
            chunks = self._parse_document(doc)
            if not chunks:
                logger.warning(
                    "Structural parser produced 0 chunks for %s, falling back",
                    doc.metadata.get("document_number", "?"),
                )
                # Fallback: return the whole document as a single chunk
                chunks = [doc]
            all_chunks.extend(chunks)
        logger.info("StructuralVietnameseChunker produced %d total chunks", len(all_chunks))
        return all_chunks

    def _parse_document(self, doc: Document) -> list[Document]:
        """Parse one document into chunks based on legal structure."""
        text = doc.page_content
        base_meta = dict(doc.metadata)

        ctx = _StructuralContext(
            document_title=base_meta.get("title", ""),
            document_number=base_meta.get("document_number", ""),
        )

        # Step 1: Extract all Điều blocks
        dieu_blocks = self._split_into_dieu(text)
        if not dieu_blocks:
            return []

        # Step 2: Parse hierarchy context (Chương, Mục) from the preamble
        preamble = dieu_blocks[0][0] if dieu_blocks else ""
        self._parse_hierarchy_from_preamble(preamble, ctx)

        chunks: list[Document] = []
        for dieu_text, dieu_num, dieu_title in dieu_blocks:
            if not dieu_num:
                # This is preamble text — update hierarchy context
                self._update_hierarchy_context(dieu_text, ctx)
                continue

            ctx.dieu = dieu_num
            ctx.dieu_title = dieu_title
            ctx.khoan = ""
            ctx.diem = ""

            # Step 3: Split Điều into Khoản blocks
            khoan_blocks = self._split_into_khoan(dieu_text)

            if not khoan_blocks:
                # Điều has no numbered clauses — emit as single chunk
                chunk = self._make_chunk(dieu_text, ctx, base_meta)
                chunks.append(chunk)
            else:
                for khoan_text, khoan_num in khoan_blocks:
                    ctx.khoan = khoan_num
                    ctx.diem = ""

                    # Step 4: Check for Điểm within the Khoản
                    diem_blocks = self._split_into_diem(khoan_text)

                    if not diem_blocks:
                        # Khoản has no lettered points — emit as single chunk
                        chunk = self._make_chunk(khoan_text, ctx, base_meta)
                        chunks.append(chunk)
                    else:
                        # Emit the whole Khoản as one chunk (keeps Điểm together)
                        chunk = self._make_chunk(khoan_text, ctx, base_meta)
                        # Annotate with point info
                        point_labels = [d[1] for d in diem_blocks]
                        chunk.metadata["points"] = ",".join(point_labels)
                        chunks.append(chunk)

        # Update hierarchy for each chunk (Chương/Mục might change between Điều)
        self._assign_hierarchy_context(chunks, text, ctx)

        return chunks

    def _split_into_dieu(self, text: str) -> list[tuple[str, str, str]]:
        """Split text into (block_text, dieu_number, dieu_title) tuples.

        The first tuple may have dieu_number="" for preamble text.
        """
        matches = list(_RE_DIEU.finditer(text))
        if not matches:
            return []

        blocks: list[tuple[str, str, str]] = []

        # Preamble before first Điều
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                blocks.append((preamble, "", ""))

        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[m.start() : end].strip()
            dieu_num = m.group(1)
            dieu_title = m.group(2).strip() if m.group(2) else ""
            blocks.append((block, dieu_num, dieu_title))

        return blocks

    def _split_into_khoan(self, dieu_text: str) -> list[tuple[str, str]]:
        """Split a Điều block into (khoan_text, khoan_number) tuples."""
        # Only match Khoản that start at the beginning of a line
        lines = dieu_text.split("\n")
        khoan_blocks: list[tuple[str, str]] = []
        current_lines: list[str] = []
        current_num = ""

        for line in lines:
            m = _RE_KHOAN.match(line)
            if m and not current_num:
                # Skip lines before first Khoản (Điều header)
                current_num = m.group(1)
                current_lines = [line]
            elif m:
                # Save previous Khoản and start new one
                khoan_blocks.append(("\n".join(current_lines), current_num))
                current_num = m.group(1)
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_num and current_lines:
            khoan_blocks.append(("\n".join(current_lines), current_num))

        return khoan_blocks

    def _split_into_diem(self, khoan_text: str) -> list[tuple[str, str]]:
        """Split a Khoản block into (diem_text, diem_label) tuples."""
        matches = list(_RE_DIEM.finditer(khoan_text))
        if not matches:
            return []

        blocks: list[tuple[str, str]] = []
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(khoan_text)
            block = khoan_text[m.start() : end].strip()
            blocks.append((block, m.group(1)))

        return blocks

    def _update_hierarchy_context(self, text: str, ctx: _StructuralContext) -> None:
        """Update Chương/Mục context from a text block."""
        for line in text.split("\n"):
            line = line.strip()
            if _RE_CHUONG.match(line):
                # Grab the chapter line + the next non-empty line as title
                ctx.chuong = line
            elif _RE_MUC.match(line):
                ctx.muc = line
            elif _RE_PHAN.match(line):
                ctx.phan = line

    def _parse_hierarchy_from_preamble(self, preamble: str, ctx: _StructuralContext) -> None:
        """Parse Chương/Mục from text appearing before the first Điều."""
        self._update_hierarchy_context(preamble, ctx)

    def _assign_hierarchy_context(
        self, chunks: list[Document], full_text: str, ctx: _StructuralContext
    ) -> None:
        """Walk through the full text to assign Chương/Mục to each chunk.

        This handles the case where Chương/Mục headers appear between Điều blocks.
        """
        # Build a map: line_number → hierarchy context
        lines = full_text.split("\n")
        current_chuong = ""
        current_muc = ""
        chuong_title = ""
        muc_title = ""

        hierarchy_at_dieu: dict[str, tuple[str, str]] = {}

        for i, line in enumerate(lines):
            stripped = line.strip()
            if _RE_CHUONG.match(stripped):
                current_chuong = stripped
                # Try to get the title from the next line
                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_line = lines[i + 1].strip()
                    if not _RE_DIEU.match(next_line) and not _RE_MUC.match(next_line):
                        chuong_title = next_line
                        current_chuong = f"{stripped} - {chuong_title}"
                current_muc = ""  # Reset Mục when new Chương starts
            elif _RE_MUC.match(stripped):
                current_muc = stripped
                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_line = lines[i + 1].strip()
                    if not _RE_DIEU.match(next_line):
                        muc_title = next_line
                        current_muc = f"{stripped}. {muc_title}"

            m = _RE_DIEU.match(stripped)
            if m:
                dieu_num = m.group(1)
                hierarchy_at_dieu[dieu_num] = (current_chuong, current_muc)

        # Apply to chunks
        for chunk in chunks:
            dieu_num = chunk.metadata.get("article", "")
            if dieu_num in hierarchy_at_dieu:
                ch, mu = hierarchy_at_dieu[dieu_num]
                chunk.metadata["chapter"] = ch
                chunk.metadata["section"] = mu

            # Build and apply title chain
            if self.enrich_title:
                title_parts: list[str] = []
                doc_title = chunk.metadata.get("title", "")
                if doc_title:
                    title_parts.append(f"[{doc_title}]")
                ch_val = chunk.metadata.get("chapter", "")
                if ch_val:
                    title_parts.append(f"[{ch_val}]")
                mu_val = chunk.metadata.get("section", "")
                if mu_val:
                    title_parts.append(f"[{mu_val}]")
                art = chunk.metadata.get("article", "")
                art_title = chunk.metadata.get("article_title", "")
                if art:
                    art_str = f"Điều {art}"
                    if art_title:
                        art_str += f". {art_title}"
                    title_parts.append(f"[{art_str}]")

                title_chain = " → ".join(title_parts)
                chunk.metadata["title_chain"] = title_chain

                # Prepend title chain to page_content for better embeddings
                if title_chain:
                    chunk.page_content = f"{title_chain}\n{chunk.page_content}"

    def _make_chunk(
        self, text: str, ctx: _StructuralContext, base_meta: dict
    ) -> Document:
        """Create a Document chunk with enriched metadata."""
        meta = dict(base_meta)
        meta["article"] = ctx.dieu
        meta["article_title"] = ctx.dieu_title
        meta["clause"] = ctx.khoan
        meta["point"] = ctx.diem
        meta["chapter"] = ctx.chuong
        meta["section"] = ctx.muc

        # Generate stable chunk_id based on content
        id_source = f"{ctx.document_number}:art{ctx.dieu}:cl{ctx.khoan}:pt{ctx.diem}"
        meta["chunk_id"] = hashlib.sha256(id_source.encode()).hexdigest()[:16]

        return Document(page_content=text.strip(), metadata=meta)


__all__ = ["TextChunker", "RecursiveVietnameseChunker", "StructuralVietnameseChunker"]
