"""
Document chunker — splits paper text into overlapping chunks
suitable for embedding and retrieval.
Preserves section/page provenance on every chunk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    token_count: Optional[int] = None
    start_char: int = 0
    end_char: int = 0


def _estimate_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token."""
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    chunk_size: int = 512,       # tokens
    chunk_overlap: int = 64,     # tokens
    page_number: Optional[int] = None,
    section_title: Optional[str] = None,
) -> List[TextChunk]:
    """
    Split text into overlapping chunks.
    Tries to split on sentence boundaries to preserve coherence.
    Returns chunks with all provenance fields populated.
    """
    if not text or not text.strip():
        return []

    # Convert token targets to char targets (rough: 4 chars/token)
    char_size = chunk_size * 4
    char_overlap = chunk_overlap * 4

    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return []

    chunks: List[TextChunk] = []
    current_chars: List[str] = []
    current_len = 0
    chunk_idx = 0
    global_offset = 0

    for sentence in sentences:
        s_len = len(sentence)

        if current_len + s_len > char_size and current_chars:
            # Emit current chunk
            content = " ".join(current_chars)
            chunks.append(
                TextChunk(
                    content=content,
                    chunk_index=chunk_idx,
                    page_number=page_number,
                    section_title=section_title,
                    token_count=_estimate_tokens(content),
                    start_char=global_offset,
                    end_char=global_offset + len(content),
                )
            )
            chunk_idx += 1
            global_offset += len(content) + 1

            # Overlap: keep last N chars worth of sentences
            overlap_chars = 0
            kept = []
            for s in reversed(current_chars):
                if overlap_chars + len(s) > char_overlap:
                    break
                kept.insert(0, s)
                overlap_chars += len(s) + 1

            current_chars = kept
            current_len = overlap_chars

        current_chars.append(sentence)
        current_len += s_len + 1

    # Emit remaining content
    if current_chars:
        content = " ".join(current_chars)
        chunks.append(
            TextChunk(
                content=content,
                chunk_index=chunk_idx,
                page_number=page_number,
                section_title=section_title,
                token_count=_estimate_tokens(content),
                start_char=global_offset,
                end_char=global_offset + len(content),
            )
        )

    return chunks


def chunk_sections(
    sections: List[dict],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[TextChunk]:
    """
    Chunk a list of section dicts: [{title, content, page_start}, ...]
    Returns a flat list of chunks with section provenance.
    """
    all_chunks: List[TextChunk] = []
    global_idx = 0
    for section in sections:
        section_chunks = chunk_text(
            text=section.get("content", ""),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            page_number=section.get("page_start"),
            section_title=section.get("title"),
        )
        for chunk in section_chunks:
            chunk.chunk_index = global_idx
            global_idx += 1
            all_chunks.append(chunk)
    return all_chunks
