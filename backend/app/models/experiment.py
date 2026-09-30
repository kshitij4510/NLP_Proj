"""
Experiment, ExperimentRun, Metric, Dataset models.
Every run records full reproducibility metadata (spec §3 Experiment Layer).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text, Enum as SAEnum
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Dataset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "datasets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[Optional[str]] = mapped_column(String(100))
    size_info: Mapped[Optional[dict]] = mapped_column(JSONB)
    splits: Mapped[Optional[dict]] = mapped_column(JSONB)
    license: Mapped[Optional[str]] = mapped_column(String(200))
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)


class Experiment(Base, UUIDMixin, TimestampMixin):
    """
    Experiment specification (spec §3 Experiment Layer).
    Captures full reproducibility metadata before any run.
    """
    __tablename__ = "experiments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    hypothesis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="SET NULL"), nullable=True
    )
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, name="experiment_status"),
        default=ExperimentStatus.DRAFT,
        nullable=False,
    )

    # Specification (spec §3 Experiment Layer)
    model_spec: Mapped[Optional[dict]] = mapped_column(JSONB)       # model, architecture
    baseline_spec: Mapped[Optional[dict]] = mapped_column(JSONB)    # baseline model
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSONB)
    random_seed: Mapped[Optional[int]] = mapped_column(Integer)
    preprocessing_steps: Mapped[Optional[list]] = mapped_column(JSONB)
    evaluation_metrics: Mapped[Optional[list]] = mapped_column(JSONB)
    ablations: Mapped[Optional[list]] = mapped_column(JSONB)
    statistical_tests: Mapped[Optional[list]] = mapped_column(JSONB)
    hardware_requirements: Mapped[Optional[dict]] = mapped_column(JSONB)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="experiments")
    hypothesis: Mapped[Optional["Hypothesis"]] = relationship("Hypothesis", back_populates="experiments")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset")
    runs: Mapped[List["ExperimentRun"]] = relationship(
        "ExperimentRun", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentRun(Base, UUIDMixin, TimestampMixin):
    """
    A single execution of an Experiment.
    Every run records full provenance (spec §3 Experiment Layer).
    """
    __tablename__ = "experiment_runs"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, name="experiment_status"),
        default=ExperimentStatus.QUEUED,
        nullable=False,
    )
    # Reproducibility
    git_commit: Mapped[Optional[str]] = mapped_column(String(40))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    runtime_seconds: Mapped[Optional[float]] = mapped_column(Float)
    hardware_info: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Config snapshot at run time
    model_config_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    hyperparameter_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Results
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB)
    artifacts: Mapped[Optional[list]] = mapped_column(JSONB)
    logs: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="runs")
    result_metrics: Mapped[List["Metric"]] = relationship(
        "Metric", back_populates="run", cascade="all, delete-orphan"
    )


class Metric(Base, UUIDMixin):
    __tablename__ = "metrics"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiment_runs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    split: Mapped[Optional[str]] = mapped_column(String(50))
    step: Mapped[Optional[int]] = mapped_column(Integer)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)

    run: Mapped["ExperimentRun"] = relationship("ExperimentRun", back_populates="result_metrics")
