"""Retained local tasks with persisted terminal states; no Redis worker required."""
import asyncio
import uuid
from app.core.logging import get_logger

logger = get_logger(__name__)
_tasks = {}

async def recover_interrupted_jobs():
    from sqlalchemy import update
    from app.database.session import AsyncSessionLocal
    from app.models.job import ResearchJob, JobStatus
    async with AsyncSessionLocal() as db:
        await db.execute(update(ResearchJob).where(ResearchJob.status.in_([
            JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING])).values(
                status=JobStatus.FAILED, error_message="Local server stopped before this job finished. Run the pipeline again."))
        await db.commit()

async def _execute(project_id, job_id, stage, kind, kwargs):
    from app.database.session import AsyncSessionLocal
    from app.agents.workflow_runner import WorkflowRunner
    from app.repositories.job_repo import JobRepository
    from app.ingestion.ingestion_pipeline import IngestionPipeline
    from app.models.job import JobStatus
    async with AsyncSessionLocal() as db:
        try:
            if kind == "pipeline":
                await WorkflowRunner(db).run(job_id=job_id, project_id=project_id, start_stage=stage)
            else:
                jobs = JobRepository(db)
                await jobs.mark_started(job_id)
                await db.commit()
                pipeline = IngestionPipeline(db)
                if kind == "discovery":
                    result = await pipeline.run_discovery(project_id, kwargs["query"], sources=kwargs.get("sources"))
                else:
                    result = await pipeline.run_ingestion(project_id, paper_id=kwargs.get("paper_id"), batch_size=200)
                await jobs.update(job_id, job_metadata={"output": result})
                await jobs.mark_completed(job_id)
            await db.commit()
        except asyncio.CancelledError:
            await db.rollback()
            await JobRepository(db).update(job_id, status=JobStatus.CANCELLED)
            await db.commit()
        except Exception as exc:
            await db.rollback()
            await JobRepository(db).update(job_id, status=JobStatus.FAILED, error_message=str(exc)[:4000])
            await db.commit()
            logger.exception("local_job.failed", job_id=str(job_id))

def enqueue(project_id, job_id, stage, kind="pipeline", **kwargs):
    task = asyncio.create_task(_execute(project_id, job_id, stage, kind, kwargs))
    _tasks[str(job_id)] = task
    task.add_done_callback(lambda done: _tasks.pop(str(job_id), None))
    return f"local-{job_id}"

def cancel(job_id):
    task = _tasks.get(str(job_id))
    if task:
        task.cancel()
