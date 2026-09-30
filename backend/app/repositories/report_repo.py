"""Report and citation repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.report import Citation, CitationStyle, Report, ReportStatus
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model_class = Report

    async def get_with_citations(self, report_id: uuid.UUID) -> Optional[Report]:
        result = await self.db.execute(
            select(Report)
            .options(selectinload(Report.citations))
            .where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Report], int]:
        return await self.list(
            project_id=project_id,
            offset=offset,
            limit=limit,
            order_by=Report.updated_at.desc(),
        )

    async def get_latest_completed(self, project_id: uuid.UUID) -> Optional[Report]:
        result = await self.db.execute(
            select(Report)
            .where(
                Report.project_id == project_id,
                Report.status == ReportStatus.COMPLETED,
            )
            .order_by(Report.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class CitationRepository(BaseRepository[Citation]):
    model_class = Citation

    async def list_by_report(
        self,
        report_id: uuid.UUID,
        *,
        style: Optional[CitationStyle] = None,
    ) -> List[Citation]:
        query = select(Citation).where(Citation.report_id == report_id)
        if style:
            query = query.where(Citation.style == style)
        result = await self.db.execute(query.order_by(Citation.id))
        return list(result.scalars().all())

    async def delete_by_report(self, report_id: uuid.UUID) -> int:
        return await self.delete_where(report_id=report_id)
