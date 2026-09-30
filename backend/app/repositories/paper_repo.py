"""Paper, PaperChunk, PaperSection, PaperAuthor repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import selectinload

from app.models.paper import Paper, PaperAuthor, PaperChunk, PaperSection, PaperStatus
from app.repositories.base import BaseRepository


class PaperRepository(BaseRepository[Paper]):
    model_class = Paper

    async def get_with_authors(self, paper_id: uuid.UUID) -> Optional[Paper]:
        result = await self.db.execute(
            select(Paper)
            .options(selectinload(Paper.authors))
            .where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def get_full(self, paper_id: uuid.UUID) -> Optional[Paper]:
        """Load paper with authors, sections, chunks."""
        result = await self.db.execute(
            select(Paper)
            .options(
                selectinload(Paper.authors),
                selectinload(Paper.sections),
            )
            .where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        status: Optional[PaperStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Paper], int]:
        query = select(Paper).options(selectinload(Paper.authors)).where(
            Paper.project_id == project_id
        )
        count_q = select(func.count()).select_from(Paper).where(
            Paper.project_id == project_id
        )
        if status:
            query = query.where(Paper.status == status)
            count_q = count_q.where(Paper.status == status)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(
            query.order_by(Paper.relevance_score.desc().nullslast(), Paper.year.desc().nullslast())
            .offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_doi(self, project_id: uuid.UUID, doi: str) -> Optional[Paper]:
        result = await self.db.execute(
            select(Paper).where(and_(Paper.project_id == project_id, Paper.doi == doi))
        )
        return result.scalar_one_or_none()

    async def get_by_arxiv_id(self, project_id: uuid.UUID, arxiv_id: str) -> Optional[Paper]:
        result = await self.db.execute(
            select(Paper).where(
                and_(Paper.project_id == project_id, Paper.arxiv_id == arxiv_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_ingestion(
        self, project_id: uuid.UUID, limit: int = 20
    ) -> List[Paper]:
        result = await self.db.execute(
            select(Paper)
            .where(
                and_(
                    Paper.project_id == project_id,
                    Paper.status == PaperStatus.DISCOVERED,
                    Paper.pdf_url.isnot(None),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, paper_id: uuid.UUID, status: PaperStatus) -> None:
        await self.update(paper_id, status=status)


class PaperChunkRepository(BaseRepository[PaperChunk]):
    model_class = PaperChunk

    async def list_by_paper(
        self, paper_id: uuid.UUID, *, offset: int = 0, limit: int = 200
    ) -> List[PaperChunk]:
        result = await self.db.execute(
            select(PaperChunk)
            .where(PaperChunk.paper_id == paper_id)
            .order_by(PaperChunk.chunk_index)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_project_without_embeddings(
        self, project_id: uuid.UUID, limit: int = 500
    ) -> List[PaperChunk]:
        """Return chunks that need embeddings computed."""
        result = await self.db.execute(
            select(PaperChunk)
            .join(Paper, PaperChunk.paper_id == Paper.id)
            .where(
                and_(
                    Paper.project_id == project_id,
                    PaperChunk.embedding.is_(None),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_chunks_by_ids(self, chunk_ids: List[uuid.UUID]) -> List[PaperChunk]:
        result = await self.db.execute(
            select(PaperChunk).where(PaperChunk.id.in_(chunk_ids))
        )
        return list(result.scalars().all())

    async def bulk_update_embeddings(
        self, updates: List[Tuple[uuid.UUID, List[float]]]
    ) -> int:
        """
        Update embeddings for multiple chunks in one round-trip.
        updates = [(chunk_id, embedding_vector), ...]
        """
        count = 0
        for chunk_id, embedding in updates:
            await self.update(chunk_id, embedding=embedding)
            count += 1
        return count

    async def vector_search(
        self,
        project_id: uuid.UUID,
        query_embedding: List[float],
        top_k: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[Tuple[PaperChunk, float]]:
        """
        pgvector cosine similarity search within a project.
        Returns (chunk, distance) pairs ordered by similarity.
        """
        # Build base query using pgvector's <=> operator (cosine distance)
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        query = (
            select(
                PaperChunk,
                (PaperChunk.embedding.cosine_distance(query_embedding)).label("distance"),
            )
            .join(Paper, PaperChunk.paper_id == Paper.id)
            .where(
                and_(
                    Paper.project_id == project_id,
                    PaperChunk.embedding.isnot(None),
                )
            )
        )

        if year_min is not None:
            query = query.where(Paper.year >= year_min)
        if year_max is not None:
            query = query.where(Paper.year <= year_max)

        query = query.order_by(text("distance")).limit(top_k)
        result = await self.db.execute(query)
        rows = result.all()
        return [(row[0], 1.0 - row[1]) for row in rows]  # convert distance → similarity


class PaperSectionRepository(BaseRepository[PaperSection]):
    model_class = PaperSection

    async def list_by_paper(self, paper_id: uuid.UUID) -> List[PaperSection]:
        result = await self.db.execute(
            select(PaperSection)
            .where(PaperSection.paper_id == paper_id)
            .order_by(PaperSection.position)
        )
        return list(result.scalars().all())


class PaperAuthorRepository(BaseRepository[PaperAuthor]):
    model_class = PaperAuthor

    async def list_by_paper(self, paper_id: uuid.UUID) -> List[PaperAuthor]:
        result = await self.db.execute(
            select(PaperAuthor)
            .where(PaperAuthor.paper_id == paper_id)
            .order_by(PaperAuthor.position)
        )
        return list(result.scalars().all())
