"""
Report and Citation models.
Citations are always generated from stored metadata — never fabricated by LLM.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text, Enum as SAEnum
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class CitationStyle(str, enum.Enum):
    APA = "apa"
    IEEE = "ieee"
    BIBTEX = "bibtex"


class Report(Base, UUIDMixin, TimestampMixin):
    """
    Full research report with all required sections (spec §3 Report Layer).
    Claim verification must pass before status → COMPLETED.
    """
    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"),
        default=ReportStatus.DRAFT,
        nullable=False,
    )

    # Report sections (spec §3 Report Layer)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    research_question_section: Mapped[Optional[str]] = mapped_column(Text)
    background: Mapped[Optional[str]] = mapped_column(Text)
    literature_review: Mapped[Optional[str]] = mapped_column(Text)
    research_landscape: Mapped[Optional[str]] = mapped_column(Text)
    method_comparison: Mapped[Optional[str]] = mapped_column(Text)
    research_gaps_section: Mapped[Optional[str]] = mapped_column(Text)
    hypotheses_section: Mapped[Optional[str]] = mapped_column(Text)
    experimental_design: Mapped[Optional[str]] = mapped_column(Text)
    results: Mapped[Optional[str]] = mapped_column(Text)
    ablation_study: Mapped[Optional[str]] = mapped_column(Text)
    limitations: Mapped[Optional[str]] = mapped_column(Text)
    future_work: Mapped[Optional[str]] = mapped_column(Text)
    conclusion: Mapped[Optional[str]] = mapped_column(Text)

    # Verification summary
    verification_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Number of unsupported claims — must be 0 or reviewed before COMPLETED
    unsupported_claim_count: Mapped[int] = mapped_column(default=0)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="reports")
    citations: Mapped[List["Citation"]] = relationship(
        "Citation", back_populates="report", cascade="all, delete-orphan"
    )


class Citation(Base, UUIDMixin):
    """
    Citation always sourced from stored paper metadata.
    LLM must never invent citation metadata (spec §3 Citation Layer).
    """
    __tablename__ = "citations"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    style: Mapped[CitationStyle] = mapped_column(
        SAEnum(CitationStyle, name="citation_style"),
        nullable=False,
    )
    formatted_citation: Mapped[str] = mapped_column(Text, nullable=False)
    in_text_citation: Mapped[Optional[str]] = mapped_column(String(200))
    # Raw metadata snapshot — proves the citation came from stored data
    metadata_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)

    report: Mapped["Report"] = relationship("Report", back_populates="citations")
