"""
Paper, PaperAuthor, PaperSection, and PaperChunk models.
Chunks hold vector embeddings for retrieval.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import (
    ForeignKey, Integer, String, Text, Float,
    Enum as SAEnum, UniqueConstraint,
)
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.config import settings
from app.models.base import Base, TimestampMixin, UUIDMixin

# Use pgvector when available (PostgreSQL), fall back to Text for SQLite
try:
    from pgvector.sqlalchemy import Vector as _Vector
    _EMBEDDING_COLUMN_TYPE = _Vector(settings.EMBEDDING_DIMENSION)
except Exception:
    _EMBEDDING_COLUMN_TYPE = Text()


class PaperStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Paper(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "papers"
    __table_args__ = (
        UniqueConstraint("project_id", "doi", name="uq_paper_project_doi"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    # Identifiers
    doi: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    semantic_scholar_id: Mapped[Optional[str]] = mapped_column(String(100))
    openalex_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    year: Mapped[Optional[int]] = mapped_column(Integer)
    venue: Mapped[Optional[str]] = mapped_column(String(500))
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    reference_count: Mapped[int] = mapped_column(Integer, default=0)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    local_pdf_path: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="unknown")
    status: Mapped[PaperStatus] = mapped_column(
        SAEnum(PaperStatus, name="paper_status"),
        default=PaperStatus.DISCOVERED,
        nullable=False,
    )
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relevance score from discovery
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="papers")
    authors: Mapped[List["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan",
        order_by="PaperAuthor.position"
    )
    sections: Mapped[List["PaperSection"]] = relationship(
        "PaperSection", back_populates="paper", cascade="all, delete-orphan"
    )
    chunks: Mapped[List["PaperChunk"]] = relationship(
        "PaperChunk", back_populates="paper", cascade="all, delete-orphan"
    )
    entities: Mapped[List["Entity"]] = relationship(
        "Entity", back_populates="paper", cascade="all, delete-orphan"
    )
    claims: Mapped[List["Claim"]] = relationship(
        "Claim", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper {self.title[:60]}>"


class PaperAuthor(Base, UUIDMixin):
    __tablename__ = "paper_authors"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    affiliation: Mapped[Optional[str]] = mapped_column(Text)
    orcid: Mapped[Optional[str]] = mapped_column(String(50))
    position: Mapped[int] = mapped_column(Integer, default=0)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")


class PaperSection(Base, UUIDMixin):
    __tablename__ = "paper_sections"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_type: Mapped[Optional[str]] = mapped_column(String(100))
    page_start: Mapped[Optional[int]] = mapped_column(Integer)
    page_end: Mapped[Optional[int]] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, default=0)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="sections")
    chunks: Mapped[List["PaperChunk"]] = relationship(
        "PaperChunk", back_populates="section", cascade="all, delete-orphan"
    )


class PaperChunk(Base, UUIDMixin):
    __tablename__ = "paper_chunks"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_sections.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Vector embedding — pgvector on PostgreSQL, Text fallback on SQLite
    embedding: Mapped[Optional[list]] = mapped_column(
        _EMBEDDING_COLUMN_TYPE, nullable=True
    )

    # BM25 indexed content (full-text search)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="chunks")
    section: Mapped[Optional["PaperSection"]] = relationship(
        "PaperSection", back_populates="chunks"
    )
