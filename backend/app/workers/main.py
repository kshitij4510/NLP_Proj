"""
ARQ worker entry point.
Configures worker pool, registers all tasks, enforces timeouts.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.workers.tasks import (
    run_full_pipeline,
    run_discovery_task,
    run_ingestion_task,
    run_synthesis_task,
    run_report_task,
    compute_embeddings_task,
)

configure_logging()
logger = get_logger(__name__)


async def startup(ctx: dict) -> None:
    """Worker startup hook — warm up models."""
    logger.info("worker.startup", concurrency=settings.WORKER_CONCURRENCY)
    # Pre-load embedding model so first job doesn't pay cold-start cost
    try:
        from app.nlp.embeddings import get_embedding_engine
        engine = get_embedding_engine()
        engine._load_model()
        logger.info("worker.embedding_model_ready")
    except Exception as exc:
        logger.warning("worker.embedding_warmup_failed", error=str(exc))


async def shutdown(ctx: dict) -> None:
    logger.info("worker.shutdown")


class WorkerSettings:
    """ARQ worker configuration."""

    # Register all background task functions
    functions = [
        run_full_pipeline,
        run_discovery_task,
        run_ingestion_task,
        run_synthesis_task,
        run_report_task,
        compute_embeddings_task,
    ]

    redis_settings_url = settings.REDIS_URL

    # Worker pool settings
    max_jobs = settings.WORKER_CONCURRENCY
    job_timeout = settings.JOB_TIMEOUT_SECONDS
    max_tries = settings.JOB_MAX_RETRIES + 1  # ARQ counts attempts, not retries

    # Hooks
    on_startup = startup
    on_shutdown = shutdown

    # Health
    health_check_interval = 30
    health_check_key = "researchmind_worker_health"


if __name__ == "__main__":
    import asyncio
    from arq import run_worker

    asyncio.run(run_worker(WorkerSettings))
