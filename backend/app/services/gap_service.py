"""
Research gap detection service.
Analyzes the knowledge graph and synthesis to surface genuine gaps.
Gaps are always sourced from evidence — never fabricated.
"""
from __future__ import annotations

import uuid
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.research import GapType, ResearchGap
from app.repositories.research_repo import ResearchGapRepository
from app.repositories.paper_repo import PaperRepository
from app.repositories.knowledge_repo import ClaimRepository

logger = get_logger(__name__)

GAP_PROMPT = """You are a research gap analyst. Based on the literature synthesis and evidence below, identify genuine research gaps.

Synthesis:
{synthesis}

Instructions:
- Identify gaps supported by evidence (not speculation).
- For each gap: title, description, gap_type (methodological/empirical/theoretical/application/replication/data), importance (0-1), supporting evidence quotes.
- Output JSON array of gap objects.
- Only include gaps traceable to provided evidence.
"""


class GapService:
    def __init__(self, db: AsyncSession) -> None:
        self._gaps = ResearchGapRepository(db)
        self._papers = PaperRepository(db)
        self._claims = ClaimRepository(db)

    async def detect_gaps(
        self,
        project_id: uuid.UUID,
        synthesis: dict,
        evidence_snippets: List[dict],
    ) -> List[ResearchGap]:
        """
        Detect research gaps from synthesis + evidence.
        Creates ResearchGap records with supporting paper IDs.
        """
        from app.services.llm_service import LLMService

        prompt = GAP_PROMPT.format(synthesis=str(synthesis)[:3000]) + "\nEvidence:\n" + str(evidence_snippets)[:18000]
        llm = LLMService()
        from app.core.config import settings
        if settings.LLM_PROVIDER == "demo":
            import re
            raw_gaps = []
            for snippet in evidence_snippets:
                for sentence in re.split(r"(?<=[.!?])\s+", snippet.get("content", "")):
                    if len(sentence) > 60 and re.search(r"\b(limited|limitation|limitations|however|challenge|challenges|lack)\b", sentence, re.I):
                        raw_gaps.append({"title": "Potential limitation: " + snippet.get("paper_title", "Source")[:160],
                            "description": "Potential research gap based on this source statement: " + sentence + " Coverage must be checked against further literature.",
                            "gap_type": "empirical", "importance": 0.5, "supporting_evidence": [sentence]})
                        break
                if len(raw_gaps) >= 5:
                    break
        else:
            raw_gaps = await llm.generate_json_list(prompt)

        created: List[ResearchGap] = []
        for g in raw_gaps:
            # Map supporting evidence to actual paper IDs
            supporting_ids = self._resolve_paper_ids(
                g.get("supporting_evidence", []), evidence_snippets
            )
            if not supporting_ids:
                continue
            existing = await self._gaps.first(project_id=project_id, title=g.get("title", "Unnamed gap")[:500])
            if existing:
                continue
            gap_type = self._parse_gap_type(g.get("gap_type", "empirical"))
            gap = await self._gaps.create(
                project_id=project_id,
                title=g.get("title", "Unnamed gap")[:500],
                description=g.get("description", ""),
                gap_type=gap_type,
                importance_score=float(g.get("importance", 0.5)),
                supporting_paper_ids=[str(pid) for pid in supporting_ids],
                evidence_snippets=g.get("supporting_evidence", []),
                detected_by="synthesis",
            )
            created.append(gap)

        logger.info(
            "gaps.detected",
            project_id=str(project_id),
            count=len(created),
        )
        return created

    async def list_gaps(
        self, project_id: uuid.UUID, gap_type: GapType | None = None
    ) -> Tuple[List[ResearchGap], int]:
        return await self._gaps.list_by_project(project_id, gap_type=gap_type)

    @staticmethod
    def _resolve_paper_ids(evidence_quotes: List[str], snippets: List[dict]) -> List[str]:
        ids: List[str] = []
        for s in snippets:
            paper_id = s.get("paper_id")
            content = s.get("content", "")
            if paper_id and any(q[:50] in content for q in evidence_quotes if q):
                ids.append(str(paper_id))
        return list(set(ids))

    @staticmethod
    def _parse_gap_type(raw: str) -> GapType:
        mapping = {t.value: t for t in GapType}
        return mapping.get(raw.lower(), GapType.EMPIRICAL)
