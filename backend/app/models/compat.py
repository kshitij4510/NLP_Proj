"""
Database compatibility layer.
Provides SQLite-safe type aliases for PostgreSQL-specific types.
In production (PostgreSQL) these are the real types.
In local dev (SQLite) they degrade to generic equivalents.
"""
from __future__ import annotations

import os

# Detect whether we're using SQLite
_db_url = os.getenv("DATABASE_URL", "")
_is_sqlite = "sqlite" in _db_url.lower()

if _is_sqlite:
    # SQLite-compatible replacements
    from sqlalchemy import String, Text, JSON
    from sqlalchemy import types as sa_types

    class _UUID(sa_types.TypeDecorator):
        """Store UUIDs as VARCHAR(36) in SQLite."""
        impl = String(36)
        cache_ok = True

        def __init__(self, as_uuid: bool = True, **kw):
            self.as_uuid = as_uuid
            super().__init__(**kw)

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            return str(value)

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            if self.as_uuid:
                import uuid as _uuid
                return _uuid.UUID(str(value))
            return value

    UUID = _UUID
    JSONB = JSON  # JSON is natively supported by SQLAlchemy on SQLite

else:
    # Real PostgreSQL types
    from sqlalchemy.dialects.postgresql import UUID, JSONB  # type: ignore[assignment]

__all__ = ["UUID", "JSONB"]
