"""
ResearchMind — Programmatic Research Pipeline Example.
Demonstrates end-to-end Python usage:
1. Creating a research project & formulating primary question.
2. Generating structured 10-point research plan.
3. Performing hybrid retrieval (BM25 + Dense + Reranking).
4. Extracting scientific entities and relations.
5. Detecting research gaps and generating testable hypotheses.
6. Generating citation-backed Markdown research report.
"""
import asyncio
import os
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./researchmind_local.db"
if "DATABASE_URL_SYNC" not in os.environ:
    os.environ["DATABASE_URL_SYNC"] = "sqlite:///./researchmind_local.db"

from app.database.session import AsyncSessionLocal, init_db
from app.models.project import ResearchProject, ResearchQuestion, ProjectStatus
from app.models.user import User
from app.core.security import hash_password
from app.services.research_service import ResearchService
from app.services.retrieval_service import RetrievalService
from app.services.gap_service import GapService
from app.services.hypothesis_service import HypothesisService
from app.services.report_service import ReportService
from app.schemas.retrieval import RetrievalQuery
from app.schemas.report import ReportGenerateRequest
from sqlalchemy import select


async def main():
    print("=" * 70)
    print("  ResearchMind — Autonomous Research Workflow Example")
    print("=" * 70)

    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. Ensure user exists
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(
                email="researcher@example.com",
                username="researcher",
                hashed_password=hash_password("ResearchPass123"),
            )
            db.add(user)
            await db.flush()

        # 2. Create project
        question_text = "How effective are parameter-efficient fine-tuning methods for reducing hallucination in retrieval-augmented models?"
        project = ResearchProject(
            owner_id=user.id,
            title="PEFT & RAG Factuality Investigation",
            description="Autonomous investigation into LoRA, adapter tuning, and RAG factuality.",
            status=ProjectStatus.PLANNING,
        )
        db.add(project)
        await db.flush()

        rq = ResearchQuestion(
            project_id=project.id,
            question=question_text,
            is_primary=True,
        )
        db.add(rq)
        await db.commit()

        print(f"\n[1] Project Created: {project.id}")
        print(f"    Primary Question: {question_text}")

        # 3. Generate 10-Point Research Plan (Module B)
        research_svc = ResearchService(db)
        plan = await research_svc.generate_research_plan(project.id)
        print("\n[2] Autonomous 10-Point Research Plan Generated:")
        print(f"    Problem Definition: {plan['problem_definition'][:100]}...")
        print(f"    Keywords          : {', '.join(plan['keywords'][:5])}")
        print(f"    Candidate Datasets: {', '.join(plan['candidate_datasets'][:4])}")
        print(f"    Evaluation Metrics: {', '.join(plan['metrics'][:4])}")

        # 4. Hybrid Evidence Retrieval (Module F)
        retrieval_svc = RetrievalService(db)
        results = await retrieval_svc.retrieve(
            RetrievalQuery(
                query="parameter-efficient fine-tuning retrieval augmented generation",
                project_id=project.id,
                top_k=3,
                use_reranking=True,
            )
        )
        print(f"\n[3] Hybrid Retrieval Executed ({len(results.evidence)} chunks found):")
        for i, ev in enumerate(results.evidence[:2], 1):
            print(f"    [{i}] Paper: {ev.paper_title}")
            print(f"        Score: {ev.final_score:.3f} | Dense: {ev.dense_score:.3f} | BM25: {ev.bm25_score:.3f}")

        # 5. Gap Detection & Hypothesis Generation (Modules I & J)
        gap_svc = GapService(db)
        snippets = [e.model_dump() for e in results.evidence]
        gaps = await gap_svc.detect_gaps(project.id, {"summary": "Literature synthesis"}, snippets)
        print(f"\n[4] Research Gaps Detected: {len(gaps)}")
        if gaps:
            print(f"    Sample Gap: {gaps[0].title} ({gaps[0].gap_type.value})")

            hyp_svc = HypothesisService(db)
            hyps = await hyp_svc.generate_from_gap(project.id, gaps[0].id)
            print(f"    Formulated Hypotheses: {len(hyps)}")
            if hyps:
                print(f"    Sample Hypothesis: \"{hyps[0].statement}\"")

        # 6. Generate Citation-Backed Research Report (Module T & O)
        report_svc = ReportService(db)
        report = await report_svc.generate(
            ReportGenerateRequest(
                project_id=project.id,
                verify_claims=True,
            )
        )
        markdown_text = await report_svc.to_markdown(report.id)
        print("\n[5] Structured Research Report Generated (First 350 chars):")
        print("-" * 50)
        print(markdown_text[:350] + "...\n")
        print(f"[OK] Full workflow demonstrated successfully! Report status: {report.status.value.upper()}")


if __name__ == "__main__":
    asyncio.run(main())
