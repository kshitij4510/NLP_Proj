"""
Job dispatcher — enqueues background tasks via ARQ.
Called from API routes to submit work without blocking the request.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import arq

from app.core.config import settings
from app.core.logging import get_logger
from app.models.job import JobStage

logger = get_logger(__name__)


async def _get_pool() -> arq.ArqRedis:
    return await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.REDIS_URL))


async def enqueue_full_pipeline(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    start_stage: JobStage = JobStage.PLANNING,
) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job(
        "run_full_pipeline",
        project_id=str(project_id),
        job_id=str(job_id),
        stage=start_stage.value,
    )
    logger.info(
        "dispatcher.enqueued",
        task="run_full_pipeline",
        project_id=str(project_id),
        job_id=str(job_id),
        arq_job_id=job.job_id,
    )
    return job.job_id


async def enqueue_discovery(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    query: str,
    sources: Optional[List[str]] = None,
) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job(
        "run_discovery_task",
        project_id=str(project_id),
        job_id=str(job_id),
        query=query,
        sources=sources,
    )
    return job.job_id


async def enqueue_ingestion(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    paper_id: Optional[uuid.UUID] = None,
) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job(
        "run_ingestion_task",
        project_id=str(project_id),
        job_id=str(job_id),
        paper_id=str(paper_id) if paper_id else None,
    )
    return job.job_id


async def enqueue_synthesis(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job(
        "run_synthesis_task",
        project_id=str(project_id),
        job_id=str(job_id),
    )
    return job.job_id


async def enqueue_report(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
) -> str:
    pool = await _get_pool()
    job = await pool.enqueue_job(
        "run_report_task",
        project_id=str(project_id),
        job_id=str(job_id),
    )
    return job.job_id
