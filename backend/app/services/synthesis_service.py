"""
Synthesis service — generates literature synthesis grounded in retrieved evidence.
Uses the LLM only for language generation; all claims stay linked to source chunks.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.knowledge_repo import ClaimRepository
from app.repositories.paper_repo import PaperRepository
from app.repositories.project_repo import ResearchQuestionRepository

logger = get_logger(__name__)

SYNTHESIS_PROMPT = """You are a scientific literature analyst. Based ONLY on the provided evidence snippets, write a synthesis of the research.

Research Question: {question}

Evidence Snippets:
{evidence}

Instructions:
- Summarize findings supported by the evidence.
- Every factual claim must reference its source [Paper ID: X].
- Do NOT add information not present in the evidence.
- Use academic language.
- Output structured JSON with keys: summary, key_findings, method_trends, limitations.
"""


class SynthesisService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._papers = PaperRepository(db)
        self._claims = ClaimRepository(db)
        self._questions = ResearchQuestionRepository(db)

    async def synthesize(
        self,
        project_id: uuid.UUID,
        evidence_snippets: List[dict],
    ) -> dict:
        """
        Produce a grounded literature synthesis.
        Returns structured output with provenance-linked claims.
        """
        from app.services.llm_service import LLMService

        question = await self._questions.get_primary(project_id)
        question_text = question.question if question else "Research question not set"

        evidence_text = self._format_evidence(evidence_snippets)
        prompt = SYNTHESIS_PROMPT.format(
            question=question_text,
            evidence=evidence_text,
        )

        llm = LLMService()
        raw = await llm.generate_json(prompt)

        # Tag all output as INTERPRETATION — not EVIDENCE (spec §8)
        synthesis = {
            "project_id": str(project_id),
            "research_question": question_text,
            "artifact_type": "INTERPRETATION",
            "summary": raw.get("summary", ""),
            "key_findings": raw.get("key_findings", []),
            "method_trends": raw.get("method_trends", []),
            "limitations": raw.get("limitations", []),
            "evidence_count": len(evidence_snippets),
        }

        logger.info(
            "synthesis.complete",
            project_id=str(project_id),
            evidence_count=len(evidence_snippets),
        )
        return synthesis

    @staticmethod
    def _format_evidence(snippets: List[dict]) -> str:
        parts = []
        for i, s in enumerate(snippets[:30]):  # cap to avoid context overflow
            parts.append(
                f"[{i+1}] Paper: {s.get('paper_title', 'Unknown')} "
                f"({s.get('year', '?')})\n"
                f"Section: {s.get('section_title', 'N/A')}, "
                f"Page: {s.get('page_number', 'N/A')}\n"
                f"Text: {s.get('content', '')[:500]}\n"
            )
        return "\n".join(parts)
