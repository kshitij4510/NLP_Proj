"""
Hypothesis generation and management service.
Hypotheses are grounded in research gaps — never free-form LLM invention.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.research import Hypothesis, HypothesisStatus, ResearchGap
from app.repositories.research_repo import HypothesisRepository, ResearchGapRepository
from app.schemas.research import HypothesisCreate, HypothesisRead, HypothesisUpdate

logger = get_logger(__name__)

HYPOTHESIS_PROMPT = """You are a scientific hypothesis generator.

Research Gap:
Title: {gap_title}
Description: {gap_description}
Type: {gap_type}

Supporting Evidence:
{evidence}

Generate 2-3 testable hypotheses that address this gap.
Each hypothesis must:
- Be falsifiable and testable
- Follow the format: "We hypothesize that [specific claim] because [evidence-based reasoning]"
- Include a testability_score (0-1)
- Reference supporting evidence

Output JSON array with keys: statement, rationale, testability_score.
"""


class HypothesisService:
    def __init__(self, db: AsyncSession) -> None:
        self._hypotheses = HypothesisRepository(db)
        self._gaps = ResearchGapRepository(db)

    async def generate_from_gap(
        self, project_id: uuid.UUID, gap_id: uuid.UUID
    ) -> List[Hypothesis]:
        """Generate hypotheses for a given research gap using LLM."""
        from app.services.llm_service import LLMService

        gap = await self._gaps.get_or_raise(gap_id)
        evidence = "\n".join(gap.evidence_snippets or [])
        prompt = HYPOTHESIS_PROMPT.format(
            gap_title=gap.title,
            gap_description=gap.description,
            gap_type=gap.gap_type.value,
            evidence=evidence[:2000],
        )

        llm = LLMService()
        raw = await llm.generate_json_list(prompt)

        created: List[Hypothesis] = []
        for h in raw:
            hyp = await self._hypotheses.create(
                project_id=project_id,
                gap_id=gap_id,
                statement=h.get("statement", "")[:2000],
                rationale=h.get("rationale", ""),
                status=HypothesisStatus.DRAFT,
                testability_score=float(h.get("testability_score", 0.5)),
            )
            created.append(hyp)

        logger.info(
            "hypotheses.generated",
            project_id=str(project_id),
            gap_id=str(gap_id),
            count=len(created),
        )
        return created

    async def create(
        self, project_id: uuid.UUID, data: HypothesisCreate
    ) -> Hypothesis:
        return await self._hypotheses.create(
            project_id=project_id,
            gap_id=data.gap_id,
            statement=data.statement,
            rationale=data.rationale,
            status=HypothesisStatus.DRAFT,
        )

    async def update(
        self, hypothesis_id: uuid.UUID, data: HypothesisUpdate
    ) -> Hypothesis:
        return await self._hypotheses.update(  # type: ignore[return-value]
            hypothesis_id,
            **{k: v for k, v in data.model_dump(exclude_none=True).items()},
        )

    async def list(
        self,
        project_id: uuid.UUID,
        *,
        status: Optional[HypothesisStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Hypothesis], int]:
        return await self._hypotheses.list_by_project(
            project_id, status=status, offset=offset, limit=limit
        )

    async def get(self, hypothesis_id: uuid.UUID) -> Hypothesis:
        return await self._hypotheses.get_or_raise(hypothesis_id)
