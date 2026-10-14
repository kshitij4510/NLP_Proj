"""
Temporal research analysis service.
Analyzes how literature, models, datasets, and methods evolve over time.
Spec Module R (Temporal Research Analysis).
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.knowledge import Entity, EntityType
from app.models.paper import Paper
from app.schemas.research import TemporalAnalysisRead, TemporalPoint

logger = get_logger(__name__)


class TemporalService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def analyze(self, project_id: uuid.UUID) -> TemporalAnalysisRead:
        """
        Analyze temporal trends for all papers in a project.
        Extracts papers by year, models/datasets/topics by year, and overall evolution.
        """
        # Fetch all papers for project with their years
        paper_stmt = (
            select(Paper)
            .where(Paper.project_id == project_id)
            .order_by(Paper.year.asc().nulls_last())
        )
        paper_res = await self._db.execute(paper_stmt)
        papers = list(paper_res.scalars().all())

        if not papers:
            return TemporalAnalysisRead(
                project_id=project_id,
                timeline=[],
                model_evolution=[],
                dataset_popularity=[],
                topic_trends=[],
            )

        # Fetch all extracted entities for project
        ent_stmt = select(Entity).where(Entity.project_id == project_id)
        ent_res = await self._db.execute(ent_stmt)
        entities = list(ent_res.scalars().all())

        # Map entities to papers
        entities_by_paper: Dict[uuid.UUID, List[Entity]] = defaultdict(list)
        for ent in entities:
            if ent.paper_id:
                entities_by_paper[ent.paper_id].append(ent)

        # Aggregate by year
        year_papers: Dict[int, List[Paper]] = defaultdict(list)
        for p in papers:
            if not p.year:
                continue
            year = p.year
            year_papers[year].append(p)

        timeline_points: List[TemporalPoint] = []
        all_model_counts: Counter = Counter()
        all_dataset_counts: Counter = Counter()
        model_by_year: Dict[int, Counter] = defaultdict(Counter)
        dataset_by_year: Dict[int, Counter] = defaultdict(Counter)

        for year in sorted(year_papers.keys()):
            p_list = year_papers[year]
            models = Counter()
            datasets = Counter()
            topics = Counter()

            for p in p_list:
                for ent in entities_by_paper.get(p.id, []):
                    name = ent.name.strip()
                    if ent.entity_type == EntityType.MODEL:
                        models[name] += 1
                        all_model_counts[name] += 1
                        model_by_year[year][name] += 1
                    elif ent.entity_type in (EntityType.DATASET, EntityType.BENCHMARK):
                        datasets[name] += 1
                        all_dataset_counts[name] += 1
                        dataset_by_year[year][name] += 1
                    elif ent.entity_type in (EntityType.TASK, EntityType.METHOD):
                        topics[name] += 1

                # Also extract keywords from title if any
                for word in p.title.split():
                    w = word.strip(":,.-()[]").lower()
                    if len(w) > 4 and w not in ("using", "based", "model", "neural", "learning"):
                        topics[w] += 1

            timeline_points.append(
                TemporalPoint(
                    year=year,
                    paper_count=len(p_list),
                    top_models=[m for m, _ in models.most_common(5)],
                    top_datasets=[d for d, _ in datasets.most_common(5)],
                    top_topics=[t for t, _ in topics.most_common(5)],
                )
            )

        # Format model evolution trends
        top_models = [m for m, _ in all_model_counts.most_common(6)]
        model_evolution = [
            {
                "name": model,
                "counts": {year: model_by_year[year].get(model, 0) for year in sorted(year_papers.keys())},
            }
            for model in top_models
        ]

        # Format dataset popularity
        top_datasets = [d for d, _ in all_dataset_counts.most_common(6)]
        dataset_popularity = [
            {
                "name": dataset,
                "counts": {year: dataset_by_year[year].get(dataset, 0) for year in sorted(year_papers.keys())},
            }
            for dataset in top_datasets
        ]

        # Topic trends: papers per year
        topic_trends = [
            {"year": tp.year, "papers": tp.paper_count, "topics": tp.top_topics[:3]}
            for tp in timeline_points
        ]

        logger.info(
            "temporal_service.analyzed",
            project_id=str(project_id),
            years=len(timeline_points),
        )

        return TemporalAnalysisRead(
            project_id=project_id,
            timeline=timeline_points,
            model_evolution=model_evolution,
            dataset_popularity=dataset_popularity,
            topic_trends=topic_trends,
        )
