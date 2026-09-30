"""
Background task definitions for ARQ worker.
Each task is an async function that receives an ARQ context + typed arguments.
Tasks map 1:1 to pipeline stages and job types.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional


# ── Full pipeline ──────────────────────────────────────────────────────────────

async def run_full_pipeline(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
    stage: str = "PLANNING",
) -> Dict[str, Any]:
    """
    Run the complete research pipeline from a given stage.
    Called by the API when a user triggers a full research run.
    """
    from app.agents.workflow_runner import WorkflowRunner
    from app.database.session import AsyncSessionLocal
    from app.models.job import JobStage
    from app.core.logging import get_logger

    logger = get_logger("worker.run_full_pipeline")
    logger.info("task.run_full_pipeline.start", project_id=project_id, job_id=job_id)

    async with AsyncSessionLocal() as db:
        runner = WorkflowRunner(db)
        result_ctx = await runner.run(
            job_id=uuid.UUID(job_id),
            project_id=uuid.UUID(project_id),
            start_stage=JobStage[stage],
        )

    logger.info(
        "task.run_full_pipeline.complete",
        project_id=project_id,
        status=result_ctx.status.value,
    )
    return {
        "project_id": project_id,
        "job_id": job_id,
        "status": result_ctx.status.value,
        "stage_outputs": {k: str(v) for k, v in result_ctx.stage_outputs.items()},
    }


# ── Individual stage tasks ─────────────────────────────────────────────────────

async def run_discovery_task(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
    query: str,
    sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    from app.ingestion.ingestion_pipeline import IngestionPipeline
    from app.database.session import AsyncSessionLocal
    from app.repositories.job_repo import JobRepository

    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        await job_repo.mark_started(uuid.UUID(job_id))

        pipeline = IngestionPipeline(db)
        result = await pipeline.run_discovery(
            project_id=uuid.UUID(project_id),
            query=query,
            sources=sources,
        )
        await job_repo.mark_completed(uuid.UUID(job_id))
        await db.commit()

    return result


async def run_ingestion_task(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
    paper_id: Optional[str] = None,
) -> Dict[str, Any]:
    from app.ingestion.ingestion_pipeline import IngestionPipeline
    from app.database.session import AsyncSessionLocal
    from app.repositories.job_repo import JobRepository

    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        await job_repo.mark_started(uuid.UUID(job_id))

        pipeline = IngestionPipeline(db)
        result = await pipeline.run_ingestion(
            project_id=uuid.UUID(project_id),
            paper_id=uuid.UUID(paper_id) if paper_id else None,
        )
        await job_repo.mark_completed(uuid.UUID(job_id))
        await db.commit()

    return result


async def run_synthesis_task(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
) -> Dict[str, Any]:
    from app.services.research_service import ResearchService
    from app.database.session import AsyncSessionLocal
    from app.repositories.job_repo import JobRepository

    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        await job_repo.mark_started(uuid.UUID(job_id))

        svc = ResearchService(db)
        result = await svc.run_synthesis_pipeline(
            project_id=uuid.UUID(project_id),
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # system
        )
        await job_repo.mark_completed(uuid.UUID(job_id))
        await db.commit()

    return result


async def run_report_task(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
) -> Dict[str, Any]:
    from app.services.report_service import ReportService
    from app.models.report import CitationStyle
    from app.schemas.report import ReportGenerateRequest
    from app.database.session import AsyncSessionLocal
    from app.repositories.job_repo import JobRepository

    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        await job_repo.mark_started(uuid.UUID(job_id))

        svc = ReportService(db)
        report = await svc.generate(
            ReportGenerateRequest(
                project_id=uuid.UUID(project_id),
                citation_styles=[CitationStyle.APA, CitationStyle.BIBTEX],
                verify_claims=True,
            )
        )
        await job_repo.mark_completed(uuid.UUID(job_id))
        await db.commit()

    return {"report_id": str(report.id), "status": report.status.value}


async def compute_embeddings_task(
    ctx: Dict[str, Any],
    project_id: str,
    job_id: str,
) -> Dict[str, Any]:
    """Compute missing embeddings for all chunks in a project."""
    from app.nlp.embeddings import get_embedding_engine
    from app.repositories.paper_repo import PaperChunkRepository
    from app.database.session import AsyncSessionLocal
    from app.repositories.job_repo import JobRepository

    async with AsyncSessionLocal() as db:
        job_repo = JobRepository(db)
        await job_repo.mark_started(uuid.UUID(job_id))

        chunk_repo = PaperChunkRepository(db)
        chunks = await chunk_repo.list_by_project_without_embeddings(
            uuid.UUID(project_id), limit=2000
        )

        engine = get_embedding_engine()
        texts = [c.content for c in chunks]
        embeddings = await engine.encode(texts, batch_size=32)
        updates = [(c.id, emb) for c, emb in zip(chunks, embeddings)]
        count = await chunk_repo.bulk_update_embeddings(updates)

        await job_repo.mark_completed(uuid.UUID(job_id))
        await db.commit()

    return {"embedded_chunks": count}
