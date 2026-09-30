"""
Workflow runner — drives the state machine through all pipeline stages.
Each stage: validate input → execute handler → persist output → advance state.
No infinite loops: max_retries enforced per stage, timeout enforced globally.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.stage_handlers import STAGE_HANDLERS
from app.agents.states import STAGE_TRANSITIONS, WorkflowContext, next_stage
from app.core.config import settings
from app.core.exceptions import JobMaxRetriesError, JobTimeoutError, WorkflowError
from app.core.logging import get_logger
from app.models.job import JobStage, JobStatus
from app.repositories.job_repo import JobRepository

logger = get_logger(__name__)


class WorkflowRunner:
    """
    Executes the full research pipeline for a project.
    State is persisted to DB after every stage so restarts are safe.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._job_repo = JobRepository(db)

    async def run(
        self,
        job_id: uuid.UUID,
        project_id: uuid.UUID,
        start_stage: JobStage = JobStage.PLANNING,
        stage_data: Optional[dict] = None,
    ) -> WorkflowContext:
        """
        Run the full pipeline from start_stage through COMPLETED.
        Respects JOB_TIMEOUT_SECONDS and JOB_MAX_RETRIES per stage.
        """
        ctx = WorkflowContext(
            project_id=str(project_id),
            job_id=str(job_id),
            current_stage=start_stage,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        if stage_data:
            ctx.stage_outputs.update(stage_data)

        await self._job_repo.mark_started(job_id)

        current_stage: Optional[JobStage] = start_stage

        while current_stage is not None and current_stage != JobStage.COMPLETED:
            handler = STAGE_HANDLERS.get(current_stage)
            if handler is None:
                error = f"No handler registered for stage: {current_stage.value}"
                ctx.fail(error)
                await self._job_repo.mark_failed(job_id, error)
                raise WorkflowError(error)

            stage_succeeded = False
            last_error: Optional[Exception] = None

            for attempt in range(settings.JOB_MAX_RETRIES + 1):
                try:
                    logger.info(
                        "workflow.stage_start",
                        job_id=str(job_id),
                        stage=current_stage.value,
                        attempt=attempt,
                    )

                    # Enforce per-stage timeout
                    output = await asyncio.wait_for(
                        handler(ctx, self._db),
                        timeout=settings.JOB_TIMEOUT_SECONDS,
                    )

                    ctx.record_stage_output(current_stage, output)
                    await self._persist_progress(job_id, current_stage)

                    logger.info(
                        "workflow.stage_complete",
                        job_id=str(job_id),
                        stage=current_stage.value,
                    )
                    stage_succeeded = True
                    break

                except asyncio.TimeoutError:
                    last_error = JobTimeoutError(
                        f"Stage {current_stage.value} timed out after {settings.JOB_TIMEOUT_SECONDS}s"
                    )
                    logger.warning(
                        "workflow.stage_timeout",
                        job_id=str(job_id),
                        stage=current_stage.value,
                        attempt=attempt,
                    )

                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "workflow.stage_error",
                        job_id=str(job_id),
                        stage=current_stage.value,
                        attempt=attempt,
                        error=str(exc),
                    )

                if attempt < settings.JOB_MAX_RETRIES:
                    # Exponential backoff: 2s, 4s, 8s
                    await asyncio.sleep(2 ** (attempt + 1))

            if not stage_succeeded:
                error_msg = str(last_error) if last_error else "Unknown error"
                ctx.fail(error_msg)
                await self._job_repo.mark_failed(job_id, error_msg)
                raise WorkflowError(
                    f"Stage {current_stage.value} failed after {settings.JOB_MAX_RETRIES} retries: {error_msg}"
                ) from last_error

            current_stage = next_stage(current_stage)

        ctx.complete()
        await self._job_repo.mark_completed(job_id)
        logger.info("workflow.complete", job_id=str(job_id), project_id=str(project_id))
        return ctx

    async def run_single_stage(
        self,
        job_id: uuid.UUID,
        project_id: uuid.UUID,
        stage: JobStage,
        context_data: Optional[dict] = None,
    ) -> WorkflowContext:
        """Run a single pipeline stage — useful for partial re-runs."""
        ctx = WorkflowContext(
            project_id=str(project_id),
            job_id=str(job_id),
            current_stage=stage,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        if context_data:
            ctx.stage_outputs.update(context_data)

        handler = STAGE_HANDLERS.get(stage)
        if handler is None:
            raise WorkflowError(f"No handler for stage: {stage.value}")

        output = await asyncio.wait_for(
            handler(ctx, self._db),
            timeout=settings.JOB_TIMEOUT_SECONDS,
        )
        ctx.record_stage_output(stage, output)
        return ctx

    async def _persist_progress(
        self, job_id: uuid.UUID, completed_stage: JobStage
    ) -> None:
        """Update job progress proportional to pipeline position."""
        stage_list = list(STAGE_TRANSITIONS.keys())
        total = len(stage_list)
        try:
            idx = stage_list.index(completed_stage)
            progress = (idx + 1) / total
        except ValueError:
            progress = 0.0
        await self._job_repo.update_progress(job_id, progress)
        await self._db.commit()
