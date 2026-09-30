"""Research project and research question repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.project import ProjectStatus, ResearchProject, ResearchQuestion
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[ResearchProject]):
    model_class = ResearchProject

    async def get_with_questions(self, project_id: uuid.UUID) -> Optional[ResearchProject]:
        result = await self.db.execute(
            select(ResearchProject)
            .options(selectinload(ResearchProject.research_questions))
            .where(ResearchProject.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        *,
        status: Optional[ProjectStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ResearchProject], int]:
        query = select(ResearchProject).where(ResearchProject.owner_id == owner_id)
        count_query = select(func.count()).select_from(ResearchProject).where(
            ResearchProject.owner_id == owner_id
        )
        if status:
            query = query.where(ResearchProject.status == status)
            count_query = count_query.where(ResearchProject.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(ResearchProject.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_paper_count(self, project_id: uuid.UUID) -> int:
        from app.models.paper import Paper
        result = await self.db.execute(
            select(func.count()).select_from(Paper)
            .where(Paper.project_id == project_id)
        )
        return result.scalar_one()

    async def get_hypothesis_count(self, project_id: uuid.UUID) -> int:
        from app.models.research import Hypothesis
        result = await self.db.execute(
            select(func.count()).select_from(Hypothesis)
            .where(Hypothesis.project_id == project_id)
        )
        return result.scalar_one()


class ResearchQuestionRepository(BaseRepository[ResearchQuestion]):
    model_class = ResearchQuestion

    async def get_primary(self, project_id: uuid.UUID) -> Optional[ResearchQuestion]:
        result = await self.db.execute(
            select(ResearchQuestion)
            .where(
                ResearchQuestion.project_id == project_id,
                ResearchQuestion.is_primary == True,  # noqa: E712
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> List[ResearchQuestion]:
        result = await self.db.execute(
            select(ResearchQuestion)
            .where(ResearchQuestion.project_id == project_id)
            .order_by(ResearchQuestion.created_at)
        )
        return list(result.scalars().all())
