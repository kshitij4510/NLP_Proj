"""
Knowledge graph models: entities, relationships, claims, claim evidence.
Every edge and claim retains evidence provenance.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import (
    ForeignKey, Float, Integer, String, Text,
    Enum as SAEnum,
)
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


# ── Entity types (spec §3 NLP Layer) ──────────

class EntityType(str, enum.Enum):
    MODEL = "MODEL"
    DATASET = "DATASET"
    TASK = "TASK"
    METRIC = "METRIC"
    METHOD = "METHOD"
    BENCHMARK = "BENCHMARK"
    ORGANIZATION = "ORGANIZATION"
    AUTHOR = "AUTHOR"
    CONCEPT = "CONCEPT"


# ── Relation types (spec §3 NLP Layer) ────────

class RelationType(str, enum.Enum):
    EVALUATED_ON = "evaluated_on"
    ACHIEVES = "achieves"
    IMPROVES = "improves"
    COMPARED_WITH = "compared_with"
    CITES = "cites"
    USED_FOR = "used_for"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    BASED_ON = "based_on"
    AUTHORED_BY = "authored_by"
    USES = "uses"
    COMPARES_WITH = "compares_with"


# ── Claim verification states (spec §3 Evidence) ──

class VerificationStatus(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PENDING = "PENDING"


# ── Research artifact types (spec §8) ─────────

class ArtifactType(str, enum.Enum):
    EVIDENCE = "EVIDENCE"
    INTERPRETATION = "INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT_RESULT = "EXPERIMENT_RESULT"
    USER_NOTE = "USER_NOTE"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"


class Entity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "entities"

    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chunks.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[Optional[str]] = mapped_column(Text, index=True)
    entity_type: Mapped[EntityType] = mapped_column(
        SAEnum(EntityType, name="entity_type"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    # Source span provenance
    start_char: Mapped[Optional[int]] = mapped_column(Integer)
    end_char: Mapped[Optional[int]] = mapped_column(Integer)
    context_snippet: Mapped[Optional[str]] = mapped_column(Text)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="entities")
    # Outgoing relations
    source_relations: Mapped[List["Relationship"]] = relationship(
        "Relationship", foreign_keys="[Relationship.source_entity_id]",
        back_populates="source_entity", cascade="all, delete-orphan"
    )


class Relationship(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "relationships"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    relation_type: Mapped[RelationType] = mapped_column(
        SAEnum(RelationType, name="relation_type"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    # Provenance
    paper_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chunks.id", ondelete="SET NULL"), nullable=True
    )
    evidence_snippet: Mapped[Optional[str]] = mapped_column(Text)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)

    source_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[source_entity_id], back_populates="source_relations"
    )
    target_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[target_entity_id]
    )


class Claim(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "claims"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    paper_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        SAEnum(ArtifactType, name="artifact_type"),
        default=ArtifactType.UNSUPPORTED_CLAIM,
        nullable=False,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    source_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chunks.id", ondelete="SET NULL"), nullable=True
    )
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)

    paper: Mapped[Optional["Paper"]] = relationship("Paper", back_populates="claims")
    evidence_links: Mapped[List["ClaimEvidence"]] = relationship(
        "ClaimEvidence", back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidence(Base, UUIDMixin, TimestampMixin):
    """
    Evidence Layer — every claim maps to a specific chunk, page, section.
    This is the core traceability mechanism (spec §3 Evidence Layer).
    """
    __tablename__ = "claim_evidence"

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_chunks.id", ondelete="SET NULL"), nullable=True
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_sections.id", ondelete="SET NULL"), nullable=True
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    support_type: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="verification_status"),
        nullable=False,
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="evidence_links")
