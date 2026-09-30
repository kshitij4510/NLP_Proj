"""
Research service — orchestrates the full research pipeline stages.
Coordinates: retrieval → synthesis → gap detection → hypothesis generation.
All artifacts maintain evidence provenance.
"""
from __future__ import annotations

import uuid
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.schemas.retrieval import RetrievalQuery

logger = get_logger(__name__)


class ResearchService:
    """
    High-level orchestration layer.
    Called by agents and API endpoints to run full or partial research pipelines.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def run_synthesis_pipeline(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict:
        """
        Synthesis pipeline:
        1. Retrieve evidence for the primary research question
        2. Synthesize
        3. Detect gaps
        4. Generate hypotheses per gap
        Returns a structured summary of artifacts created.
        """
        from app.services.retrieval_service import RetrievalService
        from app.services.synthesis_service import SynthesisService
        from app.services.gap_service import GapService
        from app.services.hypothesis_service import HypothesisService
        from app.repositories.project_repo import ResearchQuestionRepository

        # Step 1 — get primary research question
        q_repo = ResearchQuestionRepository(self._db)
        question = await q_repo.get_primary(project_id)
        if not question:
            return {"error": "No primary research question set"}
        query_text = question.question

        # Step 2 — retrieve evidence
        retrieval_svc = RetrievalService(self._db)
        result = await retrieval_svc.retrieve(
            RetrievalQuery(
                query=query_text,
                project_id=project_id,
                top_k=20,
                use_reranking=True,
            )
        )
        snippets = [e.model_dump() for e in result.evidence]

        # Step 3 — synthesize
        synthesis_svc = SynthesisService(self._db)
        synthesis = await synthesis_svc.synthesize(project_id, snippets)

        # Step 4 — detect gaps
        gap_svc = GapService(self._db)
        gaps = await gap_svc.detect_gaps(project_id, synthesis, snippets)

        # Step 5 — generate hypotheses for each gap
        hyp_svc = HypothesisService(self._db)
        total_hypotheses = 0
        for gap in gaps:
            hyps = await hyp_svc.generate_from_gap(project_id, gap.id)
            total_hypotheses += len(hyps)

        logger.info(
            "research.synthesis_pipeline_complete",
            project_id=str(project_id),
            evidence_count=len(snippets),
            gaps_detected=len(gaps),
            hypotheses_generated=total_hypotheses,
        )

        return {
            "synthesis": synthesis,
            "gaps_detected": len(gaps),
            "hypotheses_generated": total_hypotheses,
            "evidence_count": len(snippets),
        }

    async def get_project_summary(self, project_id: uuid.UUID) -> Dict:
        """Summarize project progress across all pipeline stages."""
        from app.repositories.paper_repo import PaperRepository
        from app.repositories.research_repo import (
            ResearchGapRepository, HypothesisRepository,
        )
        from app.repositories.experiment_repo import ExperimentRepository
        from app.repositories.report_repo import ReportRepository
        from app.repositories.knowledge_repo import ClaimRepository

        paper_repo = PaperRepository(self._db)
        gap_repo = ResearchGapRepository(self._db)
        hyp_repo = HypothesisRepository(self._db)
        exp_repo = ExperimentRepository(self._db)
        report_repo = ReportRepository(self._db)
        claim_repo = ClaimRepository(self._db)

        papers, paper_total = await paper_repo.list_by_project(project_id, limit=1)
        gaps, gap_total = await gap_repo.list_by_project(project_id, limit=1)
        hyps, hyp_total = await hyp_repo.list_by_project(project_id, limit=1)
        exps, exp_total = await exp_repo.list_by_project(project_id, limit=1)
        reports, report_total = await report_repo.list_by_project(project_id, limit=1)
        claims, claim_total = await claim_repo.list_by_project(project_id, limit=1)

        return {
            "papers": paper_total,
            "research_gaps": gap_total,
            "hypotheses": hyp_total,
            "experiments": exp_total,
            "reports": report_total,
            "claims": claim_total,
        }

    async def generate_research_plan(self, project_id: uuid.UUID) -> dict:
        """
        Generate a structured 10-field research plan (Spec Module B).
        Examines primary research question, runs LLM synthesis or sensible NLP defaults.
        """
        from app.repositories.project_repo import ProjectRepository, ResearchQuestionRepository
        from app.services.llm_service import LLMService

        q_repo = ResearchQuestionRepository(self._db)
        p_repo = ProjectRepository(self._db)
        question = await q_repo.get_primary(project_id)
        project = await p_repo.get(project_id)
        if not project:
            raise ValueError("Project not found")

        q_text = question.question if question else project.title

        llm = LLMService()
        prompt = f"""You are an autonomous AI research scientist in NLP.
Create a structured research plan for this question:
"{q_text}"

Return JSON with exact keys:
{{
  "problem_definition": "Clear concise scope of the problem",
  "sub_questions": ["3-4 concrete sub-questions"],
  "keywords": ["5-8 precise academic keywords"],
  "related_concepts": ["4-6 related theories/architectures"],
  "search_strategy": ["Query 1", "Query 2", "Query 3"],
  "inclusion_criteria": ["Peer-reviewed 2020-2024", "Empirical NLP benchmarks", "English"],
  "exclusion_criteria": ["Non-peer reviewed blogs", "Non-NLP applications"],
  "candidate_datasets": ["Benchmark 1", "Benchmark 2"],
  "metrics": ["Precision", "Recall", "F1", "Faithfulness", "Latency"],
  "potential_experiments": ["Compare baseline vs proposed method", "Ablation study"]
}}"""

        raw = await llm.generate_json(prompt)

        # Ensure realistic fallback defaults if demo mode or LLM omitted fields
        plan = {
            "research_question": q_text,
            "problem_definition": raw.get("problem_definition") or f"Systematic investigation into {q_text}.",
            "sub_questions": raw.get("sub_questions") or [
                f"What are the dominant architectures addressing {q_text}?",
                "How do recent approaches compare across standard benchmarks?",
                "What are the unresolved trade-offs between accuracy, latency, and resource constraints?",
            ],
            "keywords": raw.get("keywords") or [
                "retrieval augmented generation", "hallucination detection",
                "factual consistency", "dense retrieval", "reranking", "parameter efficient fine-tuning"
            ],
            "related_concepts": raw.get("related_concepts") or [
                "Vector Embeddings", "BM25 Ranking", "Cross-Encoder Reranking",
                "Factuality Benchmarks", "Chain-of-Thought Verification"
            ],
            "search_strategy": raw.get("search_strategy") or [
                f"{q_text} survey",
                f"{q_text} evaluation benchmark",
                f"{q_text} state of the art",
            ],
            "inclusion_criteria": raw.get("inclusion_criteria") or [
                "Peer-reviewed academic papers (ACL, EMNLP, NAACL, NeurIPS, ICLR, arXiv)",
                "Published between 2020 and 2024",
                "Contains empirical benchmark results or architectural comparisons",
            ],
            "exclusion_criteria": raw.get("exclusion_criteria") or [
                "Non-peer reviewed blog posts and opinion pieces",
                "Studies lacking quantitative evaluation or reproducible metrics",
            ],
            "candidate_datasets": raw.get("candidate_datasets") or [
                "HaluEval", "TruthfulQA", "FEVER", "TriviaQA", "Natural Questions"
            ],
            "metrics": raw.get("metrics") or [
                "Faithfulness", "Answer Relevance", "F1 Score", "ROUGE-L", "Latency (ms)", "GPU Memory"
            ],
            "potential_experiments": raw.get("potential_experiments") or [
                "Baseline LLM vs Dense RAG vs Hybrid RAG with Cross-Encoder",
                "Ablation on chunk sizes (128 vs 256 vs 512 tokens) and top-k retrieval depth",
                "Claim verification accuracy across confidence thresholds",
            ],
            "is_approved": False,
        }

        # Store in project settings
        settings_dict = dict(project.settings or {})
        settings_dict["research_plan"] = plan
        project.settings = settings_dict
        await self._db.commit()

        logger.info("research_service.plan_generated", project_id=str(project_id))
        return plan

    async def get_research_plan(self, project_id: uuid.UUID) -> Optional[dict]:
        """Fetch stored research plan for project."""
        from app.repositories.project_repo import ProjectRepository

        p_repo = ProjectRepository(self._db)
        project = await p_repo.get(project_id)
        if not project:
            return None
        settings_dict = project.settings or {}
        return settings_dict.get("research_plan")

    async def update_research_plan(self, project_id: uuid.UUID, updates: dict) -> dict:
        """Update and/or approve research plan."""
        from app.repositories.project_repo import ProjectRepository

        p_repo = ProjectRepository(self._db)
        project = await p_repo.get(project_id)
        if not project:
            raise ValueError("Project not found")

        settings_dict = dict(project.settings or {})
        current_plan = settings_dict.get("research_plan", {})
        current_plan.update({k: v for k, v in updates.items() if v is not None})
        settings_dict["research_plan"] = current_plan
        project.settings = settings_dict
        await self._db.commit()

        logger.info("research_service.plan_updated", project_id=str(project_id), approved=current_plan.get("is_approved"))
        return current_plan
