"""
Project service — owns all project and research-question business logic.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.project import ProjectStatus, ResearchProject, ResearchQuestion
from app.repositories.project_repo import ProjectRepository, ResearchQuestionRepository
from app.schemas.project import (
    ProjectCreate, ProjectDetail, ProjectRead, ProjectUpdate,
    ResearchQuestionCreate, ResearchQuestionRead,
)

logger = get_logger(__name__)


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self._projects = ProjectRepository(db)
        self._questions = ResearchQuestionRepository(db)

    # ── Projects ──────────────────────────────

    async def create(self, owner_id: uuid.UUID, data: ProjectCreate) -> ResearchProject:
        project = await self._projects.create(
            owner_id=owner_id,
            title=data.title,
            description=data.description,
            tags=data.tags or [],
            status=ProjectStatus.CREATED,
        )
        if data.research_question:
            await self._questions.create(
                project_id=project.id,
                question=data.research_question.question,
                sub_questions=data.research_question.sub_questions or [],
                scope=data.research_question.scope,
                keywords=data.research_question.keywords or [],
                is_primary=True,
            )
        logger.info("project.created", project_id=str(project.id), owner=str(owner_id))
        return project

    async def get(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ResearchProject:
        project = await self._projects.get_with_questions(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        self._check_owner(project, user_id)
        return project

    async def list(
        self,
        owner_id: uuid.UUID,
        *,
        status: Optional[ProjectStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ResearchProject], int]:
        return await self._projects.list_by_owner(
            owner_id, status=status, offset=offset, limit=limit
        )

    async def update(
        self, project_id: uuid.UUID, user_id: uuid.UUID, data: ProjectUpdate
    ) -> ResearchProject:
        project = await self._projects.get_or_raise(project_id)
        self._check_owner(project, user_id)
        updated = await self._projects.update(
            project_id,
            **{k: v for k, v in data.model_dump(exclude_none=True).items()},
        )
        return updated  # type: ignore[return-value]

    async def delete(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        project = await self._projects.get_or_raise(project_id)
        self._check_owner(project, user_id)
        await self._projects.delete(project_id)
        logger.info("project.deleted", project_id=str(project_id))

    async def get_detail(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectDetail:
        project = await self.get(project_id, user_id)
        paper_count = await self._projects.get_paper_count(project_id)
        hypothesis_count = await self._projects.get_hypothesis_count(project_id)
        questions = await self._questions.list_by_project(project_id)
        return ProjectDetail(
            **ProjectRead.model_validate(project).model_dump(),
            research_questions=[ResearchQuestionRead.model_validate(q) for q in questions],
            paper_count=paper_count,
            hypothesis_count=hypothesis_count,
            experiment_count=0,
        )

    # ── Research questions ─────────────────────

    async def add_question(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ResearchQuestionCreate,
    ) -> ResearchQuestion:
        project = await self._projects.get_or_raise(project_id)
        self._check_owner(project, user_id)
        return await self._questions.create(
            project_id=project_id,
            question=data.question,
            sub_questions=data.sub_questions or [],
            scope=data.scope,
            keywords=data.keywords or [],
            is_primary=data.is_primary,
        )

    async def list_questions(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[ResearchQuestion]:
        project = await self._projects.get_or_raise(project_id)
        self._check_owner(project, user_id)
        return await self._questions.list_by_project(project_id)

    # ── Helpers ───────────────────────────────

    @staticmethod
    def _check_owner(project: ResearchProject, user_id: uuid.UUID) -> None:
        if project.owner_id != user_id:
            raise AuthorizationError("You do not own this project")
