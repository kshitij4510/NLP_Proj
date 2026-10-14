"""
Unit tests for Report export functions (Markdown & BibTeX).
Spec Module T & §45.
"""
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ResearchProject
from app.models.report import Citation, CitationStyle, Report, ReportStatus
from app.models.user import User
from app.models.paper import Paper
from app.services.report_service import ReportService


@pytest.mark.asyncio
async def test_report_to_markdown_and_bibtex(db: AsyncSession):
    user = User(
        email="reporter@example.com",
        username="reporter_user",
        hashed_password="pw",
    )
    db.add(user)
    await db.flush()

    project = ResearchProject(
        owner_id=user.id,
        title="Hallucination Detection Survey",
    )
    db.add(project)
    await db.flush()

    paper = Paper(
        project_id=project.id,
        title="Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        year=2023,
        doi="10.48550/arXiv.2310.11511",
    )
    db.add(paper)
    await db.flush()

    report = Report(
        project_id=project.id,
        title="Autonomous Survey on Self-RAG and Hallucinations",
        status=ReportStatus.COMPLETED,
        abstract="This report reviews recent advancements in self-reflective RAG.",
        research_question_section="How does Self-RAG mitigate hallucination?",
        background="Background context on LLM factuality.",
        literature_review="Extensive literature review of 2020-2024 work.",
        unsupported_claim_count=0,
    )
    db.add(report)
    await db.flush()

    citation = Citation(
        report_id=report.id,
        paper_id=paper.id,
        style=CitationStyle.BIBTEX,
        formatted_citation="@article{asai2023selfrag, title={Self-RAG}, author={Asai et al.}, year={2023}}",
        in_text_citation="Asai et al. (2023)",
        metadata_snapshot={"title": paper.title, "year": paper.year, "authors": ["Asai et al."]},
    )
    db.add(citation)
    await db.commit()

    svc = ReportService(db)

    # Test Markdown conversion
    md = await svc.to_markdown(report.id)
    assert "# Autonomous Survey on Self-RAG and Hallucinations" in md
    assert "## Abstract" in md
    assert "## References" in md
    assert "Self-RAG" in md

    # Test BibTeX export
    bib = await svc.to_bibtex(report.id)
    assert "@misc{" in bib
    assert "title = {Self-RAG:" in bib
    assert "year = {2023}" in bib
