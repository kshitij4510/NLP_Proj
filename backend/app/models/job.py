"""
ResearchJob model — tracks all background pipeline jobs.
No infinite loops: max_retries is enforced.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, Enum as SAEnum
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class JobStage(str, enum.Enum):
    PLANNING = "PLANNING"
    DISCOVERY = "DISCOVERY"
    INGESTION = "INGESTION"
    ANALYSIS = "ANALYSIS"
    EXTRACTION = "EXTRACTION"
    SYNTHESIS = "SYNTHESIS"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT_DESIGN = "EXPERIMENT_DESIGN"
    VERIFICATION = "VERIFICATION"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ResearchJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    stage: Mapped[JobStage] = mapped_column(
        SAEnum(JobStage, name="job_stage"), nullable=False, index=True
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    job_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    # ARQ / Celery job ID for tracking
    worker_job_id: Mapped[Optional[str]] = mapped_column(String(255))

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="jobs")

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries
