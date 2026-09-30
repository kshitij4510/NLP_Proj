"""Project CRUD and research question endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DB
from app.models.project import ProjectStatus
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.project import (
    ProjectCreate, ProjectDetail, ProjectRead, ProjectUpdate,
    ResearchQuestionCreate, ResearchQuestionRead,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, user: CurrentUser, db: DB):
    svc = ProjectService(db)
    project = await svc.create(user.id, data)
    # Return detail to avoid lazy-load on research_questions
    detail = await svc.get_detail(project.id, user.id)
    return detail


@router.get("", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    user: CurrentUser,
    db: DB,
    status_filter: Optional[ProjectStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    svc = ProjectService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list(user.id, status=status_filter, offset=offset, limit=page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ProjectService(db)
    return await svc.get_detail(project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(project_id: uuid.UUID, data: ProjectUpdate, user: CurrentUser, db: DB):
    svc = ProjectService(db)
    return await svc.update(project_id, user.id, data)


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ProjectService(db)
    await svc.delete(project_id, user.id)
    return SuccessResponse(message="Project deleted")


@router.post("/{project_id}/questions", response_model=ResearchQuestionRead, status_code=201)
async def add_question(
    project_id: uuid.UUID, data: ResearchQuestionCreate, user: CurrentUser, db: DB
):
    svc = ProjectService(db)
    return await svc.add_question(project_id, user.id, data)


@router.get("/{project_id}/questions", response_model=List[ResearchQuestionRead])
async def list_questions(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ProjectService(db)
    return await svc.list_questions(project_id, user.id)
