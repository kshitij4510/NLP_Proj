"""Research project and research question models."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Text, Enum as SAEnum
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProjectStatus(str, enum.Enum):
    CREATED = "created"
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResearchProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status"),
        default=ProjectStatus.CREATED,
        nullable=False,
    )
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    research_questions: Mapped[List["ResearchQuestion"]] = relationship(
        "ResearchQuestion", back_populates="project", cascade="all, delete-orphan"
    )
    papers: Mapped[List["Paper"]] = relationship(
        "Paper", back_populates="project", cascade="all, delete-orphan"
    )
    hypotheses: Mapped[List["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="project", cascade="all, delete-orphan"
    )
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment", back_populates="project", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[List["ResearchJob"]] = relationship(
        "ResearchJob", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ResearchProject {self.title[:40]}>"


class ResearchQuestion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_questions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    sub_questions: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    scope: Mapped[Optional[str]] = mapped_column(Text)
    keywords: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    is_primary: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    project: Mapped["ResearchProject"] = relationship(
        "ResearchProject", back_populates="research_questions"
    )

    def __repr__(self) -> str:
        return f"<ResearchQuestion {self.question[:60]}>"
