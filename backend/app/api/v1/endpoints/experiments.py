"""Experiment and run endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, Depends, APIRouter, Query, status

from app.api.deps import CurrentUser, DB, require_project_access
from app.models.experiment import ExperimentStatus
from app.schemas.common import PaginatedResponse
from app.schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentRunRead
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"], dependencies=[Depends(require_project_access)])


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    project_id: uuid.UUID, data: ExperimentCreate, user: CurrentUser, db: DB
):
    svc = ExperimentService(db)
    return await svc.create(project_id, data)


@router.post("/design/{hypothesis_id}", response_model=ExperimentRead, status_code=201)
async def design_from_hypothesis(
    project_id: uuid.UUID, hypothesis_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Auto-design an experiment from a hypothesis."""
    svc = ExperimentService(db)
    return await svc.design_from_hypothesis(project_id, hypothesis_id)


@router.get("", response_model=PaginatedResponse[ExperimentRead])
async def list_experiments(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    status_filter: Optional[ExperimentStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    svc = ExperimentService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list(project_id, status=status_filter, offset=offset, limit=page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{experiment_id}", response_model=ExperimentRead)
async def get_experiment(
    project_id: uuid.UUID, experiment_id: uuid.UUID, user: CurrentUser, db: DB
):
    svc = ExperimentService(db)
    experiment = await svc.get(experiment_id)
    if experiment.project_id != project_id:
        raise HTTPException(404, "Experiment not found")
    return await svc.get(experiment_id)


@router.post("/{experiment_id}/runs", response_model=ExperimentRunRead, status_code=201)
async def record_run(
    project_id: uuid.UUID,
    experiment_id: uuid.UUID,
    payload: Dict[str, Any],
    user: CurrentUser,
    db: DB,
):
    """Record a completed experiment run with metrics and provenance."""
    svc = ExperimentService(db)
    experiment = await svc.get(experiment_id)
    if experiment.project_id != project_id:
        raise HTTPException(404, "Experiment not found")
    return await svc.record_run(
        experiment_id=experiment_id,
        metrics=payload.get("metrics", {}),
        git_commit=payload.get("git_commit"),
        runtime_seconds=payload.get("runtime_seconds"),
        hardware_info=payload.get("hardware_info"),
        logs=payload.get("logs"),
    )


@router.get("/{experiment_id}/runs", response_model=PaginatedResponse[ExperimentRunRead])
async def list_runs(
    project_id: uuid.UUID,
    experiment_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    svc = ExperimentService(db)
    experiment = await svc.get(experiment_id)
    if experiment.project_id != project_id:
        raise HTTPException(404, "Experiment not found")
    offset = (page - 1) * page_size
    items, total = await svc.list_runs(experiment_id, offset=offset, limit=page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)
