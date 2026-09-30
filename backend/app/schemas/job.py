"""Job status schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.models.job import JobStage, JobStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class JobRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    stage: JobStage
    status: JobStatus
    progress: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    error_message: Optional[str]


class JobStatusUpdate(BaseSchema):
    """Internal — used by workers to update job state."""
    status: JobStatus
    progress: Optional[float] = None
    error_message: Optional[str] = None
