"""
Experiment service — design, tracking, and result recording.
Every experiment is fully specified before execution; runs record complete provenance.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.experiment import Experiment, ExperimentRun, ExperimentStatus
from app.repositories.experiment_repo import (
    ExperimentRepository, ExperimentRunRepository, MetricRepository,
)
from app.schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentRunRead

logger = get_logger(__name__)

EXPERIMENT_DESIGN_PROMPT = """You are an ML experiment designer.

Hypothesis:
{hypothesis}

Gap Type: {gap_type}

Propose an experiment design with:
- model: architecture recommendation
- baseline: suitable baseline
- dataset: appropriate dataset
- metrics: evaluation metrics
- hyperparameters: sensible defaults
- statistical_tests: appropriate tests
- ablations: useful ablation studies

Output JSON matching the experiment schema.
"""


class ExperimentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._experiments = ExperimentRepository(db)
        self._runs = ExperimentRunRepository(db)
        self._metrics = MetricRepository(db)

    async def design_from_hypothesis(
        self, project_id: uuid.UUID, hypothesis_id: uuid.UUID
    ) -> Experiment:
        """Auto-design an experiment specification from a hypothesis."""
        from app.services.llm_service import LLMService
        from app.repositories.research_repo import HypothesisRepository

        hyp_repo = HypothesisRepository(self._db)
        hyp = await hyp_repo.get_or_raise(hypothesis_id)
        if hyp.project_id != project_id:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Hypothesis not found in project")
        existing = await self._experiments.first(project_id=project_id, hypothesis_id=hypothesis_id)
        if existing:
            return existing

        gap_type = "unknown"
        if hyp.gap_id:
            from app.repositories.research_repo import ResearchGapRepository
            gap_repo = ResearchGapRepository(self._db)
            gap = await gap_repo.get(hyp.gap_id)
            if gap:
                gap_type = gap.gap_type.value

        prompt = EXPERIMENT_DESIGN_PROMPT.format(
            hypothesis=hyp.statement, gap_type=gap_type
        )
        llm = LLMService()
        from app.core.config import settings
        if settings.LLM_PROVIDER == "demo":
            raw = {"model": {"architecture": "Hybrid BM25 + vector retrieval; optional reranking"},
                "baseline": {"architecture": "BM25-only retrieval"},
                "metrics": ["Recall@10", "nDCG@10", "MRR"],
                "hyperparameters": {"top_k": 10, "dense_weight": 0.5, "annotation_required": True},
                "statistical_tests": ["Paired bootstrap over independently annotated queries"],
                "ablations": [{"name": "without_dense"}, {"name": "without_reranking"}]}
        else:
            raw = await llm.generate_json(prompt)

        exp = await self._experiments.create(
            project_id=project_id,
            hypothesis_id=hypothesis_id,
            title=f"Experiment: {hyp.statement[:100]}",
            description=f"Auto-designed to test: {hyp.statement}",
            model_spec=raw.get("model"),
            baseline_spec=raw.get("baseline"),
            hyperparameters=raw.get("hyperparameters"),
            evaluation_metrics=raw.get("metrics", []),
            ablations=raw.get("ablations", []),
            statistical_tests=raw.get("statistical_tests", []),
            status=ExperimentStatus.DRAFT,
        )
        logger.info(
            "experiment.designed",
            experiment_id=str(exp.id),
            hypothesis_id=str(hypothesis_id),
        )
        return exp

    async def create(
        self, project_id: uuid.UUID, data: ExperimentCreate
    ) -> Experiment:
        return await self._experiments.create(
            project_id=project_id,
            **data.model_dump(exclude_none=True),
            status=ExperimentStatus.DRAFT,
        )

    async def get(self, experiment_id: uuid.UUID) -> Experiment:
        return await self._experiments.get_or_raise(experiment_id)

    async def list(
        self,
        project_id: uuid.UUID,
        *,
        status: Optional[ExperimentStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Experiment], int]:
        return await self._experiments.list_by_project(
            project_id, status=status, offset=offset, limit=limit
        )

    async def record_run(
        self,
        experiment_id: uuid.UUID,
        metrics: Dict[str, Any],
        git_commit: Optional[str] = None,
        runtime_seconds: Optional[float] = None,
        hardware_info: Optional[dict] = None,
        logs: Optional[str] = None,
    ) -> ExperimentRun:
        """Record a completed experiment run with full provenance."""
        run = await self._runs.create(
            experiment_id=experiment_id,
            status=ExperimentStatus.COMPLETED,
            git_commit=git_commit,
            metrics=metrics,
            runtime_seconds=runtime_seconds,
            hardware_info=hardware_info,
            logs=logs,
        )
        await self._experiments.update(experiment_id, status=ExperimentStatus.COMPLETED)
        # Persist individual metric records for querying
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                await self._metrics.create(run_id=run.id, name=name, value=float(value))

        logger.info(
            "experiment.run_recorded",
            experiment_id=str(experiment_id),
            run_id=str(run.id),
            metric_count=len(metrics),
        )
        return run

    async def list_runs(
        self, experiment_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> Tuple[List[ExperimentRun], int]:
        return await self._runs.list_by_experiment(
            experiment_id, offset=offset, limit=limit
        )
