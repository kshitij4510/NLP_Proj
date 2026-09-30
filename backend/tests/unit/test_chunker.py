"""Unit tests for the text chunker."""
import pytest
from app.nlp.chunker import chunk_text, chunk_sections


def test_chunk_text_basic():
    text = "This is sentence one. This is sentence two. This is sentence three."
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.content
        assert chunk.chunk_index >= 0


def test_chunk_text_empty():
    chunks = chunk_text("", chunk_size=512)
    assert chunks == []


def test_chunk_text_preserves_page():
    text = "Some content here about transformers and attention mechanisms."
    chunks = chunk_text(text, page_number=5, section_title="Methods")
    for chunk in chunks:
        assert chunk.page_number == 5
        assert chunk.section_title == "Methods"


def test_chunk_sections():
    sections = [
        {"title": "Abstract", "content": "This paper proposes a new method.", "page_start": 1},
        {"title": "Introduction", "content": "Neural networks have revolutionized AI.", "page_start": 2},
    ]
    chunks = chunk_sections(sections, chunk_size=50)
    assert len(chunks) >= 2
    # Chunk indices should be sequential
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_text_token_count():
    text = "Word " * 100
    chunks = chunk_text(text)
    for chunk in chunks:
        assert chunk.token_count is not None
        assert chunk.token_count > 0
