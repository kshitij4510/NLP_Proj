"""
Paper ingestion pipeline — coordinates:
  discovery → download → PDF extraction → NLP extraction → embedding

Runs as a background job; updates paper status throughout.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.ingestion.academic_apis import discover_papers
from app.ingestion.downloader import download_pdf
from app.ingestion.pdf_processor import extract_pdf
from app.models.paper import PaperStatus
from app.nlp.extraction_pipeline import ExtractionPipeline
from app.repositories.paper_repo import PaperRepository
from app.services.paper_service import PaperService

logger = get_logger(__name__)


class IngestionPipeline:
    """
    Full paper ingestion pipeline.
    Each stage updates paper status for observability.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._paper_repo = PaperRepository(db)

    async def run_discovery(
        self,
        project_id: uuid.UUID,
        query: str,
        limit_per_source: int = 15,
        sources: Optional[List[str]] = None,
    ) -> dict:
        """
        Stage 1: Discover papers from academic APIs.
        Returns summary of papers added.
        """
        results = await discover_papers(query, limit_per_source, sources)

        paper_svc = PaperService(self._db)
        # Use system user id 0 equivalent — this is called from a worker, not a user request
        added, skipped = await paper_svc.ingest_from_search_results(project_id, results)

        logger.info(
            "ingestion.discovery_complete",
            project_id=str(project_id),
            discovered=len(results),
            added=added,
            skipped=skipped,
        )
        return {"discovered": len(results), "added": added, "skipped": skipped}

    async def run_ingestion(
        self,
        project_id: uuid.UUID,
        paper_id: Optional[uuid.UUID] = None,
        batch_size: int = 5,
    ) -> dict:
        """
        Stage 2+3: Download PDFs and run extraction.
        If paper_id is provided, ingests only that paper.
        Otherwise ingests all pending papers in the project.
        """
        if paper_id:
            papers = [await self._paper_repo.get_or_raise(paper_id)]
        else:
            papers = await self._paper_repo.get_pending_ingestion(
                project_id, limit=batch_size
            )

        processed = 0
        failed = 0

        for paper in papers:
            try:
                await self._ingest_single_paper(paper, project_id)
                processed += 1
            except Exception as exc:
                logger.error(
                    "ingestion.paper_failed",
                    paper_id=str(paper.id),
                    error=str(exc),
                )
                await self._paper_repo.update_status(paper.id, PaperStatus.FAILED)
                failed += 1

        logger.info(
            "ingestion.batch_complete",
            project_id=str(project_id),
            processed=processed,
            failed=failed,
        )
        return {"processed": processed, "failed": failed}

    async def _ingest_single_paper(self, paper, project_id: uuid.UUID) -> None:
        paper_id = paper.id

        # Step 1 — Download PDF
        if not paper.pdf_url:
            logger.info("ingestion.no_pdf_url", paper_id=str(paper_id))
            await self._paper_repo.update_status(paper_id, PaperStatus.SKIPPED)
            return

        await self._paper_repo.update_status(paper_id, PaperStatus.DOWNLOADING)
        local_path = await download_pdf(paper.pdf_url, paper_id)
        await self._paper_repo.update(paper_id, local_pdf_path=local_path, status=PaperStatus.DOWNLOADED)

        # Step 2 — Extract PDF structure
        await self._paper_repo.update_status(paper_id, PaperStatus.PROCESSING)
        pdf_doc = extract_pdf(local_path)

        # Update paper metadata from PDF if not already set
        if pdf_doc.abstract and not paper.abstract:
            await self._paper_repo.update(paper_id, abstract=pdf_doc.abstract)

        # Step 3 — NLP extraction (chunking, embedding, NER, relations)
        sections = [
            {
                "title": s.title,
                "content": s.content,
                "section_type": s.section_type,
                "page_start": s.page_start,
                "page_end": s.page_end,
            }
            for s in pdf_doc.sections
            if s.content.strip()
        ]

        extraction = ExtractionPipeline(self._db)
        stats = await extraction.process_paper(
            paper_id=paper_id,
            project_id=project_id,
            sections=sections,
        )

        await self._paper_repo.update(
            paper_id,
            status=PaperStatus.PROCESSED,
            raw_metadata={
                **(paper.raw_metadata or {}),
                "extraction_stats": stats,
                "page_count": pdf_doc.page_count,
                "keyphrases": stats.get("keyphrases", []),
            },
        )

        logger.info(
            "ingestion.paper_processed",
            paper_id=str(paper_id),
            chunks=stats.get("chunks", 0),
            entities=stats.get("entities", 0),
            relations=stats.get("relations", 0),
        )
