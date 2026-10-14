"""
Paper service — manages paper metadata, deduplication, and status.
Does NOT handle PDF ingestion (that lives in ingestion/).
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.paper import Paper, PaperStatus
from app.repositories.paper_repo import (
    PaperAuthorRepository, PaperChunkRepository,
    PaperRepository, PaperSectionRepository,
)
from app.repositories.project_repo import ProjectRepository
from app.schemas.paper import PaperCreate, PaperRead, PaperSearchResult

logger = get_logger(__name__)


class PaperService:
    def __init__(self, db: AsyncSession) -> None:
        self._papers = PaperRepository(db)
        self._chunks = PaperChunkRepository(db)
        self._sections = PaperSectionRepository(db)
        self._authors = PaperAuthorRepository(db)
        self._projects = ProjectRepository(db)

    async def add_paper(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        data: PaperCreate,
    ) -> Paper:
        """Manually add a paper by DOI, arXiv ID, or PDF URL."""
        await self._assert_project_access(project_id, user_id)
        await self._assert_no_duplicate(project_id, data)

        paper = await self._papers.create(
            project_id=project_id,
            doi=data.doi,
            arxiv_id=data.arxiv_id,
            pdf_url=str(data.pdf_url) if data.pdf_url else None,
            title=data.title or "Untitled",
            status=PaperStatus.DISCOVERED,
            source="manual",
        )
        logger.info("paper.added", paper_id=str(paper.id), project_id=str(project_id))
        return paper

    async def ingest_from_search_results(
        self,
        project_id: uuid.UUID,
        results: List[PaperSearchResult],
    ) -> Tuple[int, int]:
        """
        Bulk-create papers from discovery results.
        Returns (added, skipped) counts.
        """
        added, skipped = 0, 0
        for r in results:
            # Deduplication by DOI or arXiv ID
            existing = None
            if r.doi:
                existing = await self._papers.get_by_doi(project_id, r.doi)
            if existing is None and r.arxiv_id:
                existing = await self._papers.get_by_arxiv_id(project_id, r.arxiv_id)

            if existing is None:
                existing = await self._papers.first(project_id=project_id, title=r.title)
            if existing:
                skipped += 1
                continue

            paper = await self._papers.create(
                project_id=project_id,
                doi=r.doi,
                arxiv_id=r.arxiv_id,
                title=r.title,
                abstract=r.abstract,
                year=r.year,
                venue=r.venue,
                pdf_url=r.pdf_url,
                citation_count=r.citation_count or 0,
                source=r.source,
                relevance_score=r.relevance_score,
                status=PaperStatus.DISCOVERED,
                raw_metadata={"external_id": r.external_id},
            )
            # Create authors
            for i, name in enumerate(r.authors or []):
                await self._authors.create(paper_id=paper.id, name=name, position=i)
            added += 1

        logger.info(
            "papers.ingested_from_search",
            project_id=str(project_id),
            added=added,
            skipped=skipped,
        )
        return added, skipped

    async def get(
        self, paper_id: uuid.UUID, user_id: uuid.UUID
    ) -> Paper:
        paper = await self._papers.get_with_authors(paper_id)
        if not paper:
            raise NotFoundError(f"Paper {paper_id} not found")
        await self._assert_project_access(paper.project_id, user_id)
        return paper

    async def list(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        status: Optional[PaperStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Paper], int]:
        await self._assert_project_access(project_id, user_id)
        return await self._papers.list_by_project(
            project_id, status=status, offset=offset, limit=limit
        )

    async def delete(self, paper_id: uuid.UUID, user_id: uuid.UUID) -> None:
        paper = await self._papers.get_or_raise(paper_id)
        await self._assert_project_access(paper.project_id, user_id)
        await self._papers.delete(paper_id)

    async def get_chunks_without_embeddings(
        self, project_id: uuid.UUID, limit: int = 500
    ) -> list:
        return await self._chunks.list_by_project_without_embeddings(project_id, limit)

    # ── Helpers ───────────────────────────────

    async def _assert_project_access(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        project = await self._projects.get_or_raise(project_id)
        if project.owner_id != user_id:
            raise AuthorizationError("Access denied to this project")

    async def _assert_no_duplicate(
        self, project_id: uuid.UUID, data: PaperCreate
    ) -> None:
        if data.doi:
            existing = await self._papers.get_by_doi(project_id, data.doi)
            if existing:
                raise ConflictError(f"Paper with DOI {data.doi} already exists in project")
        if data.arxiv_id:
            existing = await self._papers.get_by_arxiv_id(project_id, data.arxiv_id)
            if existing:
                raise ConflictError(f"Paper with arXiv ID {data.arxiv_id} already exists")
