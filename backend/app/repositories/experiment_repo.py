"""Experiment, ExperimentRun, Metric, Dataset repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.experiment import (
    Dataset, Experiment, ExperimentRun, ExperimentStatus, Metric,
)
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    model_class = Dataset

    async def list_by_project(
        self, project_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> Tuple[List[Dataset], int]:
        return await self.list(project_id=project_id, offset=offset, limit=limit)


class ExperimentRepository(BaseRepository[Experiment]):
    model_class = Experiment

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        status: Optional[ExperimentStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Experiment], int]:
        query = select(Experiment).where(Experiment.project_id == project_id)
        count_q = select(func.count()).select_from(Experiment).where(
            Experiment.project_id == project_id
        )
        if status:
            query = query.where(Experiment.status == status)
            count_q = count_q.where(Experiment.status == status)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(
            query.order_by(Experiment.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_by_hypothesis(self, hypothesis_id: uuid.UUID) -> List[Experiment]:
        result = await self.db.execute(
            select(Experiment)
            .where(Experiment.hypothesis_id == hypothesis_id)
            .order_by(Experiment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_runs(self, experiment_id: uuid.UUID) -> Optional[Experiment]:
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.runs).selectinload(ExperimentRun.result_metrics))
            .where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()


class ExperimentRunRepository(BaseRepository[ExperimentRun]):
    model_class = ExperimentRun

    async def list_by_experiment(
        self, experiment_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> Tuple[List[ExperimentRun], int]:
        return await self.list(
            experiment_id=experiment_id, offset=offset, limit=limit,
            order_by=ExperimentRun.created_at.desc(),
        )

    async def get_latest(self, experiment_id: uuid.UUID) -> Optional[ExperimentRun]:
        result = await self.db.execute(
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class MetricRepository(BaseRepository[Metric]):
    model_class = Metric

    async def list_by_run(self, run_id: uuid.UUID) -> List[Metric]:
        result = await self.db.execute(
            select(Metric)
            .where(Metric.run_id == run_id)
            .order_by(Metric.name, Metric.step)
        )
        return list(result.scalars().all())
