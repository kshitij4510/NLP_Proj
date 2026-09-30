"""
Research gap, hypothesis, research note models.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Float, String, Text, Enum as SAEnum
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class GapType(str, enum.Enum):
    METHODOLOGICAL = "methodological"
    EMPIRICAL = "empirical"
    THEORETICAL = "theoretical"
    APPLICATION = "application"
    REPLICATION = "replication"
    DATA = "data"


class HypothesisStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


class ResearchGap(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_gaps"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    gap_type: Mapped[GapType] = mapped_column(
        SAEnum(GapType, name="gap_type"), nullable=False
    )
    importance_score: Mapped[Optional[float]] = mapped_column(Float)
    supporting_paper_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    evidence_snippets: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    # Provenance — never fabricated
    detected_by: Mapped[str] = mapped_column(String(100), default="synthesis")

    hypotheses: Mapped[List["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="gap", cascade="all, delete-orphan"
    )


class Hypothesis(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "hypotheses"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    gap_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_gaps.id", ondelete="SET NULL"), nullable=True
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[HypothesisStatus] = mapped_column(
        SAEnum(HypothesisStatus, name="hypothesis_status"),
        default=HypothesisStatus.DRAFT,
        nullable=False,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    supporting_evidence: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    testability_score: Mapped[Optional[float]] = mapped_column(Float)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="hypotheses")
    gap: Mapped[Optional["ResearchGap"]] = relationship("ResearchGap", back_populates="hypotheses")
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment", back_populates="hypothesis"
    )


class ResearchNote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_notes"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    paper_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), default="general")
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
