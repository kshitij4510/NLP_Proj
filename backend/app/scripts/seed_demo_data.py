"""
Database seeder script.
Loads pre-processed foundational NLP research corpus into ResearchMind.
Spec Module 43 (Sample Data) & §52 (Final Demo Workflow).
"""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# Ensure paths
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./researchmind_local.db"
if "DATABASE_URL_SYNC" not in os.environ:
    os.environ["DATABASE_URL_SYNC"] = "sqlite:///./researchmind_local.db"

from app.core.security import hash_password
from app.database.session import AsyncSessionLocal, init_db
from app.models.knowledge import ArtifactType, Claim, ClaimEvidence, Entity, EntityType, VerificationStatus
from app.models.paper import Paper, PaperAuthor, PaperChunk, PaperSection, PaperStatus
from app.models.project import ProjectStatus, ResearchProject, ResearchQuestion
from app.models.user import User


async def seed():
    print("=" * 60)
    print("  ResearchMind — Seeding NLP Research Corpus")
    print("=" * 60)

    await init_db()

    data_file = Path(__file__).resolve().parents[3] / "data" / "processed" / "seed_papers.json"
    if not data_file.exists():
        print(f"Error: {data_file} not found")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        papers_data = json.load(f)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 1. Create or get demo user
        res = await db.execute(select(User).where(User.email == "demo@researchmind.ai"))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                email="demo@researchmind.ai",
                username="demoresearcher",
                hashed_password=hash_password("DemoPassword123"),
                full_name="Dr. ResearchMind AI",
            )
            db.add(user)
            await db.flush()
            print(f"[OK] Created user: {user.email}")
        else:
            print(f"[OK] Using existing user: {user.email}")

        # 2. Create flagship project
        p_title = "Hallucination Detection and Mitigation in Retrieval-Augmented Generation"
        res = await db.execute(select(ResearchProject).where(ResearchProject.title == p_title))
        project = res.scalar_one_or_none()

        if not project:
            project = ResearchProject(
                owner_id=user.id,
                title=p_title,
                description="Autonomous investigation into RAG architectures, atomic factuality scoring, and self-reflective mitigation of hallucinations in LLMs.",
                status=ProjectStatus.ACTIVE,
                tags=["RAG", "hallucination", "verification", "PEFT", "factuality"],
            )
            db.add(project)
            await db.flush()

            # Primary research question
            rq = ResearchQuestion(
                project_id=project.id,
                question="How effective are retrieval-augmented generation systems and atomic verification methods at detecting and reducing hallucinations in large language models?",
                is_primary=True,
                keywords=["retrieval augmented generation", "hallucination detection", "factuality", "self-reflection"],
            )
            db.add(rq)
            await db.flush()
            print(f"[OK] Created flagship project: {project.title}")
        else:
            print(f"[OK] Project already exists: {project.title}")

        # 3. Seed papers, sections, chunks, entities, and claims
        seeded_papers = 0
        total_chunks = 0
        total_entities = 0
        total_claims = 0

        for p_dict in papers_data:
            # Check if paper already exists
            p_check = await db.execute(
                select(Paper).where(Paper.project_id == project.id, Paper.title == p_dict["title"])
            )
            if p_check.scalar_one_or_none():
                continue

            paper = Paper(
                project_id=project.id,
                title=p_dict["title"],
                abstract=p_dict["abstract"],
                year=p_dict.get("year"),
                venue=p_dict.get("venue"),
                doi=p_dict.get("doi"),
                arxiv_id=p_dict.get("arxiv_id"),
                pdf_url=p_dict.get("url"),
                citation_count=p_dict.get("citation_count", 0),
                status=PaperStatus.PROCESSED,
                source="academic_seed",
            )
            db.add(paper)
            await db.flush()

            # Authors
            for ord_idx, author_name in enumerate(p_dict.get("authors", [])):
                author = PaperAuthor(
                    paper_id=paper.id,
                    name=author_name,
                    position=ord_idx,
                )
                db.add(author)

            # Sections and chunks
            sections_dict = p_dict.get("sections", {})
            first_chunk_id = None
            first_section_id = None

            for sec_idx, (sec_title, sec_content) in enumerate(sections_dict.items()):
                section = PaperSection(
                    paper_id=paper.id,
                    title=sec_title,
                    position=sec_idx,
                    content=sec_content,
                    page_start=1,
                    page_end=1,
                )
                db.add(section)
                await db.flush()
                if first_section_id is None:
                    first_section_id = section.id

                chunk = PaperChunk(
                    paper_id=paper.id,
                    section_id=section.id,
                    content=sec_content,
                    chunk_index=sec_idx,
                    token_count=len(sec_content.split()),
                    page_number=1,
                    chunk_metadata={"section_title": sec_title},
                )
                db.add(chunk)
                await db.flush()
                total_chunks += 1
                if first_chunk_id is None:
                    first_chunk_id = chunk.id

            # Entities
            for ent_data in p_dict.get("entities", []):
                ent = Entity(
                    project_id=project.id,
                    paper_id=paper.id,
                    chunk_id=first_chunk_id,
                    name=ent_data["name"],
                    entity_type=EntityType[ent_data["entity_type"]],
                    context_snippet=p_dict["title"],
                    confidence=0.95,
                )
                db.add(ent)
                total_entities += 1

            # Claims & Evidence
            for claim_data in p_dict.get("claims", []):
                claim = Claim(
                    project_id=project.id,
                    paper_id=paper.id,
                    claim_text=claim_data["statement"],
                    artifact_type=ArtifactType.EVIDENCE,
                    verification_status=VerificationStatus[claim_data["status"]],
                    confidence=0.92,
                    source_chunk_id=first_chunk_id,
                )
                db.add(claim)
                await db.flush()
                total_claims += 1

                if first_chunk_id and first_section_id:
                    evidence = ClaimEvidence(
                        claim_id=claim.id,
                        paper_id=paper.id,
                        chunk_id=first_chunk_id,
                        section_id=first_section_id,
                        support_type=VerificationStatus[claim_data["status"]],
                        relevance_score=0.92,
                        evidence_snippet=p_dict["abstract"][:300],
                        page_number=1,
                    )
                    db.add(evidence)

            seeded_papers += 1

        await db.commit()

        # 4. Generate initial research plan
        from app.services.research_service import ResearchService
        res_svc = ResearchService(db)
        plan = await res_svc.generate_research_plan(project.id)
        await res_svc.update_research_plan(project.id, {"is_approved": True})

        # 5. Seed Research Gaps
        from app.models.research import ResearchGap, GapType, Hypothesis, HypothesisStatus
        gap_check = await db.execute(select(ResearchGap).where(ResearchGap.project_id == project.id))
        if not gap_check.first():
            gap1 = ResearchGap(
                project_id=project.id,
                title="Context Degradation in Long-Sequence Retrieval-Augmented Generation",
                description="Existing RAG systems experience sharp factuality degradation when retrieved context expands past 8k tokens, leading to lost-in-the-middle hallucination patterns.",
                gap_type=GapType.EMPIRICAL,
                importance_score=0.91,
                detected_by="synthesis_engine",
            )
            gap2 = ResearchGap(
                project_id=project.id,
                title="Lack of Real-Time Falsification and Contradiction Detection in Multi-Hop RAG",
                description="Current retrieval pipelines fail to detect contradictory premises across disparate documents before passing synthesized context into generation prompts.",
                gap_type=GapType.METHODOLOGICAL,
                importance_score=0.88,
                detected_by="synthesis_engine",
            )
            gap3 = ResearchGap(
                project_id=project.id,
                title="Parameter-Efficient Alignment for Specialized Domain Knowledge Encoders",
                description="Adapting dense bi-encoders for specialized scientific vocabulary requires costly continuous pretraining without clear bounds on parameter efficiency.",
                gap_type=GapType.THEORETICAL,
                importance_score=0.82,
                detected_by="synthesis_engine",
            )
            db.add_all([gap1, gap2, gap3])
            await db.flush()

            # 6. Seed Hypotheses
            hypo1 = Hypothesis(
                project_id=project.id,
                gap_id=gap1.id,
                statement="Decomposing multi-hop retrieval passages into atomic claims before generation reduces hallucination rate by at least 15% across PopQA benchmarks.",
                rationale="Atomic isolation prevents spurious cross-attention across irrelevant retrieved spans.",
                status=HypothesisStatus.SUPPORTED,
                confidence=0.89,
                testability_score=0.94,
            )
            hypo2 = Hypothesis(
                project_id=project.id,
                gap_id=gap2.id,
                statement="Self-reflective verification tokens applied dynamically at inference prune hallucinated premises before final autoregressive generation.",
                rationale="Self-RAG demonstrates that reflection tokens suppress erroneous generation cascades.",
                status=HypothesisStatus.ACTIVE,
                confidence=0.84,
                testability_score=0.90,
            )
            db.add_all([hypo1, hypo2])
            await db.flush()

            # 7. Seed Experiments & Runs
            from app.models.experiment import Experiment, ExperimentRun, ExperimentStatus
            exp1 = Experiment(
                project_id=project.id,
                hypothesis_id=hypo1.id,
                title="Atomic Verification vs Vanilla RAG on PopQA & TriviaQA",
                description="Controlled benchmark comparing atomic claim decomposition with standard bi-encoder RAG under identical compute constraints.",
                status=ExperimentStatus.COMPLETED,
                model_spec={"architecture": "Llama-3-8B-Instruct", "framework": "PyTorch / HuggingFace"},
                hyperparameters={"learning_rate": 2e-5, "batch_size": 16, "top_k": 5},
                random_seed=42,
                evaluation_metrics=["exact_match", "f1", "hallucination_rate", "latency_ms"],
            )
            db.add(exp1)
            await db.flush()

            run1 = ExperimentRun(
                experiment_id=exp1.id,
                status=ExperimentStatus.COMPLETED,
                git_commit="4f7e2a1",
                metrics={"exact_match": 0.684, "f1": 0.792, "hallucination_rate": 0.082, "latency_ms": 142.5},
                runtime_seconds=128.4,
            )
            db.add(run1)
            await db.commit()
            print("[OK] Seeded 3 Research Gaps, 2 Hypotheses, 1 Experiment, and 1 Execution Run")

        print(f"[OK] Seeded {seeded_papers} papers")
        print(f"[OK] Seeded {total_chunks} chunks")
        print(f"[OK] Seeded {total_entities} scientific entities")
        print(f"[OK] Seeded {total_claims} verified claims with chunk evidence")
        print(f"[OK] Seeded and approved 10-field research plan")
        print("=" * 60)
        print("  Seeding Complete! Ready for Demo.")
        print(f"  Project ID: {project.id}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
