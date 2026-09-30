"""ResearchJob repository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select, update

from app.models.job import JobStage, JobStatus, ResearchJob
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[ResearchJob]):
    model_class = ResearchJob

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        stage: Optional[JobStage] = None,
        status: Optional[JobStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ResearchJob], int]:
        query = select(ResearchJob).where(ResearchJob.project_id == project_id)
        count_q = select(func.count()).select_from(ResearchJob).where(
            ResearchJob.project_id == project_id
        )
        if stage:
            query = query.where(ResearchJob.stage == stage)
            count_q = count_q.where(ResearchJob.stage == stage)
        if status:
            query = query.where(ResearchJob.status == status)
            count_q = count_q.where(ResearchJob.status == status)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(
            query.order_by(ResearchJob.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_active(self, project_id: uuid.UUID) -> Optional[ResearchJob]:
        """Return currently running job for a project, if any."""
        result = await self.db.execute(
            select(ResearchJob)
            .where(
                and_(
                    ResearchJob.project_id == project_id,
                    ResearchJob.status == JobStatus.RUNNING,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_started(self, job_id: uuid.UUID) -> None:
        await self.db.execute(
            update(ResearchJob)
            .where(ResearchJob.id == job_id)
            .values(
                status=JobStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()

    async def mark_completed(self, job_id: uuid.UUID, progress: float = 1.0) -> None:
        await self.db.execute(
            update(ResearchJob)
            .where(ResearchJob.id == job_id)
            .values(
                status=JobStatus.COMPLETED,
                progress=progress,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()

    async def mark_failed(self, job_id: uuid.UUID, error: str) -> None:
        job = await self.get(job_id)
        if job is None:
            return
        new_status = JobStatus.RETRYING if job.can_retry else JobStatus.FAILED
        await self.db.execute(
            update(ResearchJob)
            .where(ResearchJob.id == job_id)
            .values(
                status=new_status,
                error_message=error,
                retry_count=ResearchJob.retry_count + 1,
            )
        )
        await self.db.flush()

    async def update_progress(self, job_id: uuid.UUID, progress: float) -> None:
        await self.db.execute(
            update(ResearchJob)
            .where(ResearchJob.id == job_id)
            .values(progress=min(1.0, max(0.0, progress)))
        )
        await self.db.flush()

    async def get_retriable(self, limit: int = 10) -> List[ResearchJob]:
        result = await self.db.execute(
            select(ResearchJob)
            .where(
                and_(
                    ResearchJob.status == JobStatus.RETRYING,
                    ResearchJob.retry_count < ResearchJob.max_retries,
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())
