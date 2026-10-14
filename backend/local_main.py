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
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent
LOCAL_DB = (LOCAL_DIR / "researchmind_local.db").as_posix()

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── MUST set DATABASE_URL before any app module is imported ──────────────────
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{LOCAL_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{LOCAL_DB}"

os.environ.setdefault("EMBEDDING_MODEL", "lexical-hash")

from dotenv import load_dotenv
load_dotenv(LOCAL_DIR / ".env.local", override=True)

# Ensure our sqlite URL wins even if .env.local had something else
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{LOCAL_DB}"

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
    print("[OK] fakeredis active (in-process Redis)")
except ImportError as e:
    print(f"[WARN] fakeredis not available ({e}) — Redis ops will fail")

# ── Replace init_db with SQLAlchemy create_all ────────────────────────────────
async def _local_init_db():
    """Create tables via create_all — no Alembic / pg extensions needed."""
    from app.models.base import Base
    import app.models  # noqa: F401 — registers all models
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{LOCAL_DB}", echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    from app.workers.local import recover_interrupted_jobs
    await recover_interrupted_jobs()
    print("[OK] SQLite database tables created")

import app.database.session as _session_mod
_session_mod.init_db = _local_init_db

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
    port = int(os.environ.get("PORT", "8001"))
    print(f"  API Docs : http://localhost:{port}/docs")
    print(f"  Health   : http://localhost:{port}/health")
    print("=" * 62)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,   # reload causes re-import which skips patches
        log_level="info",
    )
