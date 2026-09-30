"""
Unit tests for Temporal Research Analysis Service.
Spec Module R.
"""
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Entity, EntityType
from app.models.paper import Paper
from app.models.project import ResearchProject
from app.models.user import User
from app.services.temporal_service import TemporalService


@pytest.mark.asyncio
async def test_temporal_analysis_empty(db: AsyncSession):
    svc = TemporalService(db)
    res = await svc.analyze(uuid.uuid4())
    assert res.timeline == []
    assert res.model_evolution == []


@pytest.mark.asyncio
async def test_temporal_analysis_with_data(db: AsyncSession):
    user = User(
        email="temporal@example.com",
        username="temporal_user",
        hashed_password="pw",
    )
    db.add(user)
    await db.flush()

    project = ResearchProject(
        owner_id=user.id,
        title="Evolution of NLP Architectures",
    )
    db.add(project)
    await db.flush()

    # Add papers in 2020 and 2023
    p1 = Paper(
        project_id=project.id,
        title="BERT: Pre-training of Deep Bidirectional Transformers",
        year=2020,
    )
    p2 = Paper(
        project_id=project.id,
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP",
        year=2023,
    )
    db.add_all([p1, p2])
    await db.flush()

    # Add entities
    e1 = Entity(
        project_id=project.id,
        paper_id=p1.id,
        name="BERT",
        entity_type=EntityType.MODEL,
    )
    e2 = Entity(
        project_id=project.id,
        paper_id=p2.id,
        name="DPR",
        entity_type=EntityType.MODEL,
    )
    e3 = Entity(
        project_id=project.id,
        paper_id=p2.id,
        name="Natural Questions",
        entity_type=EntityType.DATASET,
    )
    db.add_all([e1, e2, e3])
    await db.commit()

    svc = TemporalService(db)
    res = await svc.analyze(project.id)

    assert len(res.timeline) == 2
    years = [tp.year for tp in res.timeline]
    assert 2020 in years
    assert 2023 in years

    tp_2020 = next(tp for tp in res.timeline if tp.year == 2020)
    assert "BERT" in tp_2020.top_models

    tp_2023 = next(tp for tp in res.timeline if tp.year == 2023)
    assert "DPR" in tp_2023.top_models
    assert "Natural Questions" in tp_2023.top_datasets
