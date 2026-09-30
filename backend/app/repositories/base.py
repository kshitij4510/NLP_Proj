"""
Generic async repository base.
Provides CRUD operations that all domain repositories inherit.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Type-safe async repository for a SQLAlchemy model.

    Subclasses set `model_class` and gain full CRUD + pagination
    without repeating boilerplate.
    """

    model_class: Type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Create ────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelT:
        instance = self.model_class(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def create_many(self, records: List[Dict[str, Any]]) -> List[ModelT]:
        instances = [self.model_class(**r) for r in records]
        self.db.add_all(instances)
        await self.db.flush()
        return instances

    # ── Read ──────────────────────────────────

    async def get(self, id: uuid.UUID) -> Optional[ModelT]:
        result = await self.db.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: uuid.UUID) -> ModelT:
        from app.core.exceptions import NotFoundError
        instance = await self.get(id)
        if instance is None:
            raise NotFoundError(
                f"{self.model_class.__name__} {id} not found"
            )
        return instance

    async def get_many(self, ids: List[uuid.UUID]) -> List[ModelT]:
        result = await self.db.execute(
            select(self.model_class).where(self.model_class.id.in_(ids))
        )
        return list(result.scalars().all())

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Optional[Any] = None,
        **filters: Any,
    ) -> Tuple[List[ModelT], int]:
        """Return (items, total_count) with optional equality filters."""
        query = select(self.model_class)
        count_query = select(func.count()).select_from(self.model_class)

        for field, value in filters.items():
            if value is not None:
                col = getattr(self.model_class, field)
                query = query.where(col == value)
                count_query = count_query.where(col == value)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def first(self, **filters: Any) -> Optional[ModelT]:
        query = select(self.model_class)
        for field, value in filters.items():
            col = getattr(self.model_class, field)
            query = query.where(col == value)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def exists(self, **filters: Any) -> bool:
        query = select(func.count()).select_from(self.model_class)
        for field, value in filters.items():
            col = getattr(self.model_class, field)
            query = query.where(col == value)
        result = await self.db.execute(query)
        return result.scalar_one() > 0

    async def count(self, **filters: Any) -> int:
        query = select(func.count()).select_from(self.model_class)
        for field, value in filters.items():
            col = getattr(self.model_class, field)
            query = query.where(col == value)
        result = await self.db.execute(query)
        return result.scalar_one()

    # ── Update ────────────────────────────────

    async def update(self, id: uuid.UUID, **kwargs: Any) -> Optional[ModelT]:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if not kwargs:
            return await self.get(id)
        await self.db.execute(
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get(id)

    async def update_instance(self, instance: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    # ── Delete ────────────────────────────────

    async def delete(self, id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(self.model_class).where(self.model_class.id == id)
        )
        await self.db.flush()
        return result.rowcount > 0

    async def delete_where(self, **filters: Any) -> int:
        query = delete(self.model_class)
        for field, value in filters.items():
            col = getattr(self.model_class, field)
            query = query.where(col == value)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount
