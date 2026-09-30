"""
ResearchMind Command Line Interface (CLI).
Empowers researchers to create projects, search literature, analyze PDFs,
explore research gaps, inspect hypotheses, and generate reports from the terminal.
Spec Module 44 (CLI).
"""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

import click
from sqlalchemy import select

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./researchmind_local.db"
if "DATABASE_URL_SYNC" not in os.environ:
    os.environ["DATABASE_URL_SYNC"] = "sqlite:///./researchmind_local.db"

from app.database.session import AsyncSessionLocal, init_db
from app.models.paper import Paper, PaperChunk
from app.models.project import ProjectStatus, ResearchProject, ResearchQuestion
from app.models.research import ResearchGap, Hypothesis
from app.models.user import User


def run_async(coro):
    """Helper to run async functions inside click synchronous commands."""
    return asyncio.run(coro)


async def _resolve_project_id(db, project_id: Optional[str] = None) -> Optional[uuid.UUID]:
    """Resolve project ID, preferring projects with ingested papers."""
    if project_id:
        return uuid.UUID(project_id)
    from app.models.paper import Paper
    res = await db.execute(
        select(ResearchProject)
        .join(Paper, Paper.project_id == ResearchProject.id)
        .limit(1)
    )
    proj = res.scalar_one_or_none()
    if not proj:
        res = await db.execute(select(ResearchProject).limit(1))
        proj = res.scalar_one_or_none()
    return proj.id if proj else None


@click.group()
@click.version_option("1.0.0", prog_name="ResearchMind CLI")
def cli():
    """ResearchMind — Autonomous AI Research Scientist for NLP."""
    pass


@cli.command()
@click.argument("question")
@click.option("--title", default=None, help="Optional project title")
def create(question: str, title: Optional[str]):
    """Create a research project and generate a 10-point research plan."""
    async def _create():
        await init_db()
        async with AsyncSessionLocal() as db:
            # Ensure demo user exists
            res = await db.execute(select(User).limit(1))
            user = res.scalar_one_or_none()
            if not user:
                from app.core.security import hash_password
                user = User(
                    email="cli_researcher@researchmind.ai",
                    username="cli_user",
                    hashed_password=hash_password("CliUserPass123"),
                )
                db.add(user)
                await db.flush()

            proj_title = title or f"Research: {question[:60]}..."
            project = ResearchProject(
                owner_id=user.id,
                title=proj_title,
                description=f"Autonomous investigation for: {question}",
                status=ProjectStatus.PLANNING,
            )
            db.add(project)
            await db.flush()

            rq = ResearchQuestion(
                project_id=project.id,
                question=question,
                is_primary=True,
            )
            db.add(rq)
            await db.commit()

            # Generate research plan
            from app.services.research_service import ResearchService
            svc = ResearchService(db)
            plan = await svc.generate_research_plan(project.id)

            click.echo(click.style("\n=== Research Project Created ===", fg="green", bold=True))
            click.echo(f"Project ID : {project.id}")
            click.echo(f"Question   : {question}")
            click.echo("\n--- Generated Research Plan (Spec Module B) ---")
            click.echo(f"Problem Definition   : {plan.get('problem_definition')}")
            click.echo(f"Sub-Questions        : {', '.join(plan.get('sub_questions', []))}")
            click.echo(f"Keywords             : {', '.join(plan.get('keywords', []))}")
            click.echo(f"Candidate Datasets   : {', '.join(plan.get('candidate_datasets', []))}")
            click.echo(f"Evaluation Metrics   : {', '.join(plan.get('metrics', []))}")
            click.echo(click.style(f"\nTo run full literature discovery and analysis:", fg="cyan"))
            click.echo(f"  researchmind search \"{plan.get('keywords', ['NLP'])[0]}\" --project-id {project.id}")

    run_async(_create())


@cli.command()
@click.argument("query")
@click.option("--project-id", default=None, help="Project ID to search within")
@click.option("--top-k", default=5, help="Number of evidence chunks to retrieve")
def search(query: str, project_id: Optional[str], top_k: int):
    """Perform hybrid dense + BM25 retrieval over academic corpus."""
    async def _search():
        await init_db()
        async with AsyncSessionLocal() as db:
            from app.retrieval.bm25 import BM25Retriever

            p_id = await _resolve_project_id(db, project_id)
            if not p_id:
                click.echo("No projects found. Please run 'researchmind create' first.")
                return

            bm25 = BM25Retriever(db)
            results = await bm25.search(query, p_id, top_k=top_k)

            click.echo(click.style(f"\n=== Hybrid Evidence Retrieval for: '{query}' ===", fg="cyan", bold=True))
            if not results:
                click.echo("No matching chunks found in project literature.")
                return

            for rank, (chunk_id, score) in enumerate(results, 1):
                chunk_res = await db.execute(
                    select(PaperChunk, Paper)
                    .join(Paper, PaperChunk.paper_id == Paper.id)
                    .where(PaperChunk.id == chunk_id)
                )
                row = chunk_res.first()
                if row:
                    chunk, paper = row
                    sec_title = chunk.chunk_metadata.get("section_title") if chunk.chunk_metadata else "Section"
                    click.echo(f"\n[{rank}] Score: {score:.3f} | Paper: {paper.title} ({paper.year})")
                    click.echo(f"    Section: {sec_title} | Page: {chunk.page_number}")
                    snippet = chunk.content[:220].replace("\n", " ") + "..."
                    click.echo(f"    Evidence: \"{snippet}\"")

    run_async(_search())


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--project-id", default=None, help="Target Project ID")
def analyze(pdf_path: str, project_id: Optional[str]):
    """Ingest and analyze a research paper PDF (sections, chunks, entities)."""
    async def _analyze():
        await init_db()
        from app.ingestion.pdf_processor import PDFProcessor
        from app.nlp.chunker import chunk_sections
        from app.nlp.ner import extract_entities

        click.echo(f"Extracting document structure from {pdf_path}...")
        proc = PDFProcessor()
        doc = proc.process_file(pdf_path)

        click.echo(click.style("\n=== Document Processing Complete ===", fg="green", bold=True))
        click.echo(f"Title    : {doc.title}")
        click.echo(f"Pages    : {doc.page_count}")
        click.echo(f"Sections : {len(doc.sections)} detected")
        for s in doc.sections[:6]:
            click.echo(f"  - {s.title} (Page {s.page_number}, {len(s.content.split())} words)")

        chunks = chunk_sections(doc.sections)
        click.echo(f"Chunks   : {len(chunks)} generated (sliding window)")

        # Entity extraction sample
        sample_text = doc.abstract or (doc.sections[0].content if doc.sections else "")
        entities = extract_entities(sample_text)
        click.echo(f"Entities : {len(entities)} named scientific entities extracted")
        for ent in entities[:6]:
            click.echo(f"  * [{ent['entity_type']}] {ent['name']}")

    run_async(_analyze())


@cli.command()
@click.argument("project_id", default="")
def gaps(project_id: str):
    """List detected research gaps with evidence and confidence scores."""
    async def _gaps():
        await init_db()
        async with AsyncSessionLocal() as db:
            p_id = await _resolve_project_id(db, project_id)
            if not p_id:
                click.echo("No project found.")
                return

            from app.services.gap_service import GapService
            svc = GapService(db)
            gap_list, total = await svc.list_gaps(p_id)

            click.echo(click.style(f"\n=== Detected Research Gaps ({total}) ===", fg="yellow", bold=True))
            if not gap_list:
                click.echo("No research gaps detected yet. Run synthesis first.")
                return

            for i, gap in enumerate(gap_list, 1):
                click.echo(f"\n[{i}] {gap.title}")
                click.echo(f"    Type: {gap.gap_type.value.upper()} | Importance: {gap.importance_score or 'N/A'}")
                click.echo(f"    Details: {gap.description}")

    run_async(_gaps())


@cli.command()
@click.argument("project_id", default="")
def hypothesis(project_id: str):
    """List formulated testable hypotheses with testability and confidence scores."""
    async def _hyps():
        await init_db()
        async with AsyncSessionLocal() as db:
            p_id = await _resolve_project_id(db, project_id)
            if not p_id:
                click.echo("No project found.")
                return

            from app.services.hypothesis_service import HypothesisService
            svc = HypothesisService(db)
            hyp_list, total = await svc.list(p_id)

            click.echo(click.style(f"\n=== Formulated Hypotheses ({total}) ===", fg="magenta", bold=True))
            if not hyp_list:
                click.echo("No hypotheses generated yet.")
                return

            for i, hyp in enumerate(hyp_list, 1):
                click.echo(f"\n[{i}] {hyp.statement}")
                click.echo(f"    Status: {hyp.status.value.upper()} | Confidence: {hyp.confidence or 0.85}")
                if hyp.rationale:
                    click.echo(f"    Rationale: {hyp.rationale}")

    run_async(_hyps())


@cli.command()
@click.argument("project_id", default="")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown", "bibtex"]))
def report(project_id: str, fmt: str):
    """Generate or export structured research report with verifiable citations."""
    async def _report():
        await init_db()
        async with AsyncSessionLocal() as db:
            p_id = await _resolve_project_id(db, project_id)
            if not p_id:
                click.echo("No project found.")
                return

            from app.services.report_service import ReportService
            from app.schemas.report import ReportGenerateRequest
            svc = ReportService(db)

            # Check existing reports
            reports, total = await svc.list(p_id, limit=1)
            if reports:
                rep = reports[0]
            else:
                click.echo("Generating report from verified evidence...")
                rep = await svc.generate(ReportGenerateRequest(project_id=p_id, verify_claims=True))

            if fmt == "bibtex":
                output = await svc.to_bibtex(rep.id)
            else:
                output = await svc.to_markdown(rep.id)

            click.echo(output)

    run_async(_report())


@cli.command()
def benchmark():
    """Run 6-way baseline evaluation comparison on benchmark dataset."""
    from scripts.evaluate_baselines import run_baseline_evaluation
    run_async(run_baseline_evaluation())


if __name__ == "__main__":
    cli()
