"""
Job service — creates, tracks, and monitors background research jobs.
Enforces retry limits; never creates infinite loops.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import JobMaxRetriesError, JobError
from app.core.logging import get_logger
from app.models.job import JobStage, JobStatus, ResearchJob
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobRead

logger = get_logger(__name__)


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self._jobs = JobRepository(db)

    async def create(
        self,
        project_id: uuid.UUID,
        stage: JobStage,
        max_retries: int = 3,
        metadata: Optional[dict] = None,
    ) -> ResearchJob:
        job = await self._jobs.create(
            project_id=project_id,
            stage=stage,
            status=JobStatus.PENDING,
            progress=0.0,
            max_retries=max_retries,
            job_metadata=metadata or {},
        )
        logger.info(
            "job.created",
            job_id=str(job.id),
            project_id=str(project_id),
            stage=stage.value,
        )
        return job

    async def start(self, job_id: uuid.UUID) -> None:
        await self._jobs.mark_started(job_id)

    async def complete(self, job_id: uuid.UUID) -> None:
        await self._jobs.mark_completed(job_id, progress=1.0)
        logger.info("job.completed", job_id=str(job_id))

    async def fail(self, job_id: uuid.UUID, error: str) -> None:
        job = await self._jobs.get_or_raise(job_id)
        if not job.can_retry:
            raise JobMaxRetriesError(
                f"Job {job_id} exceeded max retries ({job.max_retries})"
            )
        await self._jobs.mark_failed(job_id, error)
        logger.warning("job.failed", job_id=str(job_id), error=error)

    async def update_progress(self, job_id: uuid.UUID, progress: float) -> None:
        await self._jobs.update_progress(job_id, progress)

    async def get(self, job_id: uuid.UUID) -> ResearchJob:
        return await self._jobs.get_or_raise(job_id)

    async def list(
        self,
        project_id: uuid.UUID,
        *,
        stage: Optional[JobStage] = None,
        status: Optional[JobStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ResearchJob], int]:
        return await self._jobs.list_by_project(
            project_id, stage=stage, status=status, offset=offset, limit=limit
        )

    async def get_active(self, project_id: uuid.UUID) -> Optional[ResearchJob]:
        return await self._jobs.get_active(project_id)

    async def cancel(self, job_id: uuid.UUID) -> None:
        await self._jobs.update(job_id, status=JobStatus.CANCELLED)
        logger.info("job.cancelled", job_id=str(job_id))
