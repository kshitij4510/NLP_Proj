"""Research pipeline, gaps, and hypotheses endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, APIRouter, Query, status, HTTPException

from app.api.deps import CurrentUser, DB, require_project_access
from app.models.research import GapType, HypothesisStatus
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.research import (
    HypothesisCreate, HypothesisRead, HypothesisUpdate, ResearchGapRead,
    ResearchPlan, ResearchPlanUpdate, TemporalAnalysisRead,
)
from app.services.gap_service import GapService
from app.services.hypothesis_service import HypothesisService
from app.services.job_service import JobService
from app.services.research_service import ResearchService
from app.services.temporal_service import TemporalService
from app.models.job import JobStage

router = APIRouter(prefix="/projects/{project_id}/research", tags=["research"], dependencies=[Depends(require_project_access)])


# ── Research Plan (Spec Module B) ─────────────────────────────────────────────

@router.post("/plan/generate", response_model=ResearchPlan, status_code=status.HTTP_200_OK)
async def generate_plan(project_id: uuid.UUID, user: CurrentUser, db: DB):
    """Generate structured 10-field autonomous research plan."""
    svc = ResearchService(db)
    return await svc.generate_research_plan(project_id)


@router.get("/plan", response_model=Optional[ResearchPlan])
async def get_plan(project_id: uuid.UUID, user: CurrentUser, db: DB):
    """Fetch stored research plan."""
    svc = ResearchService(db)
    plan = await svc.get_research_plan(project_id)
    if not plan:
        # Generate default plan if not yet created
        return await svc.generate_research_plan(project_id)
    return plan


@router.patch("/plan", response_model=ResearchPlan)
async def update_plan(
    project_id: uuid.UUID, data: ResearchPlanUpdate, user: CurrentUser, db: DB
):
    """Edit and/or approve the research plan."""
    svc = ResearchService(db)
    return await svc.update_research_plan(project_id, data.model_dump(exclude_unset=True))


# ── Temporal Analysis (Spec Module R) ─────────────────────────────────────────

@router.get("/temporal", response_model=TemporalAnalysisRead)
async def get_temporal_analysis(project_id: uuid.UUID, user: CurrentUser, db: DB):
    """Analyze temporal evolution of literature, models, datasets, and topics."""
    svc = TemporalService(db)
    return await svc.analyze(project_id)


@router.post("/pipeline/run", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_pipeline(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    stage: JobStage = Query(default=JobStage.PLANNING),
):
    """
    Trigger the full research pipeline as a background job.
    Returns immediately with job_id for status polling.
    """
    from app.workers.dispatcher import enqueue_full_pipeline

    from app.services.project_service import ProjectService
    await ProjectService(db).get(project_id, user.id)
    job_svc = JobService(db)
    active = await job_svc.get_active(project_id)
    if active:
        return {"job_id": str(active.id), "status": active.status.value}
    job = await job_svc.create(
        project_id=project_id,
        stage=stage,
        metadata={"triggered_by": str(user.id)},
    )
    await db.commit()
    arq_job_id = await enqueue_full_pipeline(project_id, job.id, stage)
    return {"job_id": str(job.id), "arq_job_id": arq_job_id, "status": "queued"}


@router.post("/synthesize", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def synthesize(project_id: uuid.UUID, user: CurrentUser, db: DB):
    """Trigger synthesis pipeline (retrieval → synthesis → gaps → hypotheses)."""
    from app.workers.dispatcher import enqueue_synthesis

    from app.services.project_service import ProjectService
    await ProjectService(db).get(project_id, user.id)
    job_svc = JobService(db)
    active = await job_svc.get_active(project_id)
    if active:
        return {"job_id": str(active.id), "status": active.status.value}
    job = await job_svc.create(
        project_id=project_id,
        stage=JobStage.SYNTHESIS,
        metadata={"triggered_by": str(user.id)},
    )
    await db.commit()
    await enqueue_synthesis(project_id, job.id)
    return {"job_id": str(job.id), "status": "queued"}


@router.get("/summary", response_model=dict)
async def get_summary(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ResearchService(db)
    return await svc.get_project_summary(project_id)


# ── Gaps ──────────────────────────────────────────────────────────────────────

@router.get("/gaps", response_model=PaginatedResponse[ResearchGapRead])
async def list_gaps(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    gap_type: Optional[GapType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    svc = GapService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list_gaps(project_id, gap_type)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


# ── Hypotheses ────────────────────────────────────────────────────────────────

@router.post("/hypotheses", response_model=HypothesisRead, status_code=status.HTTP_201_CREATED)
async def create_hypothesis(
    project_id: uuid.UUID, data: HypothesisCreate, user: CurrentUser, db: DB
):
    svc = HypothesisService(db)
    return await svc.create(project_id, data)


@router.get("/hypotheses", response_model=PaginatedResponse[HypothesisRead])
async def list_hypotheses(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    status_filter: Optional[HypothesisStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    svc = HypothesisService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list(project_id, status=status_filter, offset=offset, limit=page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisRead)
async def get_hypothesis(
    project_id: uuid.UUID, hypothesis_id: uuid.UUID, user: CurrentUser, db: DB
):
    svc = HypothesisService(db)
    return await svc.get(hypothesis_id)


@router.patch("/hypotheses/{hypothesis_id}", response_model=HypothesisRead)
async def update_hypothesis(
    project_id: uuid.UUID,
    hypothesis_id: uuid.UUID,
    data: HypothesisUpdate,
    user: CurrentUser,
    db: DB,
):
    svc = HypothesisService(db)
    return await svc.update(hypothesis_id, data)


@router.post("/gaps/{gap_id}/hypotheses/generate", response_model=list, status_code=201)
async def generate_hypotheses_for_gap(
    project_id: uuid.UUID, gap_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Auto-generate hypotheses for a specific research gap."""
    svc = HypothesisService(db)
    hyps = await svc.generate_from_gap(project_id, gap_id)
    return [HypothesisRead.model_validate(h) for h in hyps]
