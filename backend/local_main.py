"""
Local development entrypoint — runs without Docker, PostgreSQL, or Redis.

Patches:
  - pgvector → not needed; paper.py uses try/except and compat.py handles UUID/JSONB
  - Redis → fakeredis in-process
  - init_db → SQLAlchemy create_all (no Alembic / no pg extensions needed)
  - vector_search → falls back to recency ordering (cosine search needs PostgreSQL)

Run with:
  python local_main.py
"""
import os
import sys

# ── MUST set DATABASE_URL before any app module is imported ──────────────────
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./researchmind_local.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./researchmind_local.db"

from dotenv import load_dotenv
load_dotenv(".env.local", override=True)

# Ensure our sqlite URL wins even if .env.local had something else
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./researchmind_local.db"

# ── Patch fakeredis BEFORE any app.database import ───────────────────────────
try:
    import fakeredis
    import fakeredis.aioredis as _fake_aioredis

    _fake_server = fakeredis.FakeServer()

    class _FakeRedisWrapper:
        """Thin async-compatible wrapper around fakeredis."""
        def __init__(self):
            self._r = fakeredis.FakeRedis(server=_fake_server, decode_responses=True)

        async def setex(self, key, ttl, val):
            self._r.setex(key, ttl, val)

        async def get(self, key):
            return self._r.get(key)

        async def delete(self, *keys):
            self._r.delete(*keys)

        async def keys(self, pattern):
            return self._r.keys(pattern)

        async def ping(self):
            return True

        async def aclose(self):
            pass

    _fake_redis_instance = _FakeRedisWrapper()

    import app.database.redis as _redis_mod

    async def _fake_get_redis():
        return _fake_redis_instance

    async def _noop_close_redis():
        pass

    async def _noop_cache_set(key, value, ttl_seconds=300):
        pass

    async def _noop_cache_get(key):
        return None

    async def _noop_cache_delete(key):
        pass

    async def _noop_cache_delete_pattern(pattern):
        pass

    _redis_mod.get_redis = _fake_get_redis
    _redis_mod.close_redis = _noop_close_redis
    _redis_mod.cache_set = _noop_cache_set
    _redis_mod.cache_get = _noop_cache_get
    _redis_mod.cache_delete = _noop_cache_delete
    _redis_mod.cache_delete_pattern = _noop_cache_delete_pattern
    print("✓ fakeredis active (in-process Redis)")
except ImportError as e:
    print(f"⚠ fakeredis not available ({e}) — Redis ops will fail")

# ── Replace init_db with SQLAlchemy create_all ────────────────────────────────
async def _local_init_db():
    """Create tables via create_all — no Alembic / pg extensions needed."""
    from app.models.base import Base
    import app.models  # noqa: F401 — registers all models
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        "sqlite+aiosqlite:///./researchmind_local.db", echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✓ SQLite database tables created")

import app.database.session as _session_mod
_session_mod.init_db = _local_init_db

# ── Patch vector_search to work without pgvector ─────────────────────────────
async def _sqlite_vector_search(self, project_id, query_embedding,
                                top_k=20, year_min=None, year_max=None):
    """SQLite fallback: return latest chunks (no cosine similarity without pgvector)."""
    from sqlalchemy import select, and_
    from app.models.paper import PaperChunk, Paper

    q = (
        select(PaperChunk)
        .join(Paper, PaperChunk.paper_id == Paper.id)
        .where(Paper.project_id == project_id)
    )
    if year_min:
        q = q.where(Paper.year >= year_min)
    if year_max:
        q = q.where(Paper.year <= year_max)
    q = q.limit(top_k)
    result = await self.db.execute(q)
    chunks = list(result.scalars().all())
    return [(chunk, 0.5) for chunk in chunks]

from app.repositories.paper_repo import PaperChunkRepository
PaperChunkRepository.vector_search = _sqlite_vector_search
print("✓ Vector search patched (cosine similarity requires PostgreSQL+pgvector)")

# ── In-process async pipeline runner for local development (no Redis required) ─
import asyncio
import app.workers.dispatcher as _dispatcher
from app.models.job import JobStage

async def _local_run_pipeline_bg(project_id, job_id, initial_stage=JobStage.PLANNING):
    from app.agents.workflow_runner import WorkflowRunner
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            print(f"  [local-pipeline] Starting execution at stage {initial_stage.value}...")
            runner = WorkflowRunner(session)
            await runner.run_pipeline(project_id, job_id, initial_stage=initial_stage)
            print(f"  [local-pipeline] Completed pipeline successfully!")
        except Exception as e:
            print(f"  [local-pipeline] Execution error: {e}")

async def _local_enqueue_full_pipeline(project_id, job_id, initial_stage=JobStage.PLANNING, **kwargs):
    print(f"  [local] Spawning in-process background pipeline for project={project_id}")
    asyncio.create_task(_local_run_pipeline_bg(project_id, job_id, initial_stage))
    return f"local-job-{job_id}"

async def _local_enqueue_synthesis(project_id, job_id, **kwargs):
    print(f"  [local] Spawning in-process background synthesis for project={project_id}")
    asyncio.create_task(_local_run_pipeline_bg(project_id, job_id, initial_stage=JobStage.SYNTHESIS))
    return f"local-synth-{job_id}"

_dispatcher.enqueue_full_pipeline = _local_enqueue_full_pipeline
_dispatcher.enqueue_synthesis = _local_enqueue_synthesis
_dispatcher.enqueue_discovery = _local_enqueue_full_pipeline
_dispatcher.enqueue_ingestion = _local_enqueue_full_pipeline
_dispatcher.enqueue_report = _local_enqueue_full_pipeline
print("✓ In-process pipeline executor active (background jobs run via asyncio in local mode)")

# ── Start the server ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print()
    print("=" * 62)
    print("  ResearchMind — Local Development Mode")
    print("  Database : SQLite  (./researchmind_local.db)")
    print("  Redis    : fakeredis (in-process)")
    print("  LLM      : demo mode (no API key needed)")
    print("  Vectors  : keyword fallback (pgvector needs PostgreSQL)")
    print()
    print("  API Docs : http://localhost:8000/docs")
    print("  Health   : http://localhost:8000/health")
    print("=" * 62)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,   # reload causes re-import which skips patches
        log_level="info",
    )
