"""Job status polling endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DB
from app.models.job import JobStage, JobStatus
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.job import JobRead
from app.services.job_service import JobService

router = APIRouter(prefix="/projects/{project_id}/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobRead])
async def list_jobs(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    stage_filter: Optional[JobStage] = Query(default=None, alias="stage"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    svc = JobService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list(
        project_id,
        stage=stage_filter,
        status=status_filter,
        offset=offset,
        limit=page_size,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/active", response_model=Optional[JobRead])
async def get_active_job(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = JobService(db)
    return await svc.get_active(project_id)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(project_id: uuid.UUID, job_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = JobService(db)
    return await svc.get(job_id)


@router.post("/{job_id}/cancel", response_model=SuccessResponse)
async def cancel_job(project_id: uuid.UUID, job_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = JobService(db)
    await svc.cancel(job_id)
    return SuccessResponse(message="Job cancelled")
