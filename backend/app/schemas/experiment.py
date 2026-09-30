"""Experiment and run schemas."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.experiment import ExperimentStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ExperimentCreate(BaseSchema):
    title: str = Field(min_length=3, max_length=500)
    description: Optional[str] = None
    hypothesis_id: Optional[uuid.UUID] = None
    dataset_id: Optional[uuid.UUID] = None
    model_spec: Optional[Dict[str, Any]] = None
    baseline_spec: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    random_seed: Optional[int] = None
    preprocessing_steps: Optional[List[str]] = None
    evaluation_metrics: Optional[List[str]] = None
    ablations: Optional[List[Dict[str, Any]]] = None
    statistical_tests: Optional[List[str]] = None
    hardware_requirements: Optional[Dict[str, Any]] = None


class ExperimentRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    hypothesis_id: Optional[uuid.UUID]
    dataset_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    status: ExperimentStatus
    model_spec: Optional[Dict[str, Any]]
    hyperparameters: Optional[Dict[str, Any]]
    random_seed: Optional[int]
    evaluation_metrics: Optional[List[str]]


class ExperimentRunRead(IDSchema, TimestampSchema):
    experiment_id: uuid.UUID
    status: ExperimentStatus
    git_commit: Optional[str]
    metrics: Optional[Dict[str, Any]]
    runtime_seconds: Optional[float]
    error_message: Optional[str]
