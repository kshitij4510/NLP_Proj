"""
Async SQLAlchemy session factory.
All DB access goes through get_db() dependency.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

engine_kwargs: dict = {
    "echo": settings.DEBUG,
}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. Called at application startup."""
    from app.models.base import Base  # noqa: F401 — registers all models
    # Import all models to ensure they are registered
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            # Render's managed Postgres does not run docker/postgres/init.sql.
            for extension in ("vector", "uuid-ossp", "pg_trgm", "btree_gin"):
                await conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{extension}"'))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def close_db() -> None:
    """Dispose engine connections. Called at application shutdown."""
    await engine.dispose()
    logger.info("Database connections closed")
