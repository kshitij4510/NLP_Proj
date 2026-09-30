"""
Unit tests for Research Plan generation and approval.
Spec Module B.
"""
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ResearchProject, ResearchQuestion
from app.models.user import User
from app.services.research_service import ResearchService


@pytest.mark.asyncio
async def test_generate_and_update_research_plan(db: AsyncSession):
    # Setup user and project
    user = User(
        email="researcher@example.com",
        username="researcher1",
        hashed_password="hashedpassword123",
    )
    db.add(user)
    await db.flush()

    project = ResearchProject(
        owner_id=user.id,
        title="Hallucination Detection in Large Language Models",
        description="Investigating RAG and PEFT approaches to reduce hallucinations.",
    )
    db.add(project)
    await db.flush()

    question = ResearchQuestion(
        project_id=project.id,
        question="How effective are RAG systems at reducing hallucinations in LLMs?",
        is_primary=True,
    )
    db.add(question)
    await db.commit()

    # Generate plan
    svc = ResearchService(db)
    plan = await svc.generate_research_plan(project.id)

    assert plan["research_question"] == question.question
    assert len(plan["sub_questions"]) >= 3
    assert len(plan["keywords"]) >= 4
    assert len(plan["candidate_datasets"]) >= 2
    assert len(plan["metrics"]) >= 3
    assert len(plan["potential_experiments"]) >= 2
    assert plan["is_approved"] is False

    # Get plan
    fetched_plan = await svc.get_research_plan(project.id)
    assert fetched_plan is not None
    assert fetched_plan["research_question"] == question.question

    # Approve plan
    updated = await svc.update_research_plan(
        project.id,
        {"is_approved": True, "problem_definition": "Updated problem definition for thesis."},
    )
    assert updated["is_approved"] is True
    assert updated["problem_definition"] == "Updated problem definition for thesis."
