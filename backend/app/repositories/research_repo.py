"""Research gap, hypothesis, research note repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.research import GapType, Hypothesis, HypothesisStatus, ResearchGap, ResearchNote
from app.repositories.base import BaseRepository


class ResearchGapRepository(BaseRepository[ResearchGap]):
    model_class = ResearchGap

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        gap_type: Optional[GapType] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ResearchGap], int]:
        query = (
            select(ResearchGap)
            .where(ResearchGap.project_id == project_id)
        )
        count_q = select(func.count()).select_from(ResearchGap).where(
            ResearchGap.project_id == project_id
        )
        if gap_type:
            query = query.where(ResearchGap.gap_type == gap_type)
            count_q = count_q.where(ResearchGap.gap_type == gap_type)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(
            query.order_by(ResearchGap.importance_score.desc().nullslast())
            .offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total


class HypothesisRepository(BaseRepository[Hypothesis]):
    model_class = Hypothesis

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        status: Optional[HypothesisStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Hypothesis], int]:
        query = select(Hypothesis).where(Hypothesis.project_id == project_id)
        count_q = select(func.count()).select_from(Hypothesis).where(
            Hypothesis.project_id == project_id
        )
        if status:
            query = query.where(Hypothesis.status == status)
            count_q = count_q.where(Hypothesis.status == status)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(
            query.order_by(Hypothesis.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_by_gap(self, gap_id: uuid.UUID) -> List[Hypothesis]:
        result = await self.db.execute(
            select(Hypothesis)
            .where(Hypothesis.gap_id == gap_id)
            .order_by(Hypothesis.testability_score.desc().nullslast())
        )
        return list(result.scalars().all())


class ResearchNoteRepository(BaseRepository[ResearchNote]):
    model_class = ResearchNote

    async def list_by_project(
        self, project_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> Tuple[List[ResearchNote], int]:
        return await self.list(project_id=project_id, offset=offset, limit=limit)

    async def list_by_paper(self, paper_id: uuid.UUID) -> List[ResearchNote]:
        result = await self.db.execute(
            select(ResearchNote)
            .where(ResearchNote.paper_id == paper_id)
            .order_by(ResearchNote.created_at.desc())
        )
        return list(result.scalars().all())
