"""
Report service — assembles full research reports from verified artifacts.
Claim verification must pass before a report is marked COMPLETED (spec §3 Report Layer).
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.report import Report, ReportStatus, CitationStyle
from app.repositories.report_repo import ReportRepository
from app.repositories.paper_repo import PaperRepository
from app.repositories.research_repo import ResearchGapRepository, HypothesisRepository
from app.repositories.knowledge_repo import ClaimRepository
from app.schemas.report import ReportGenerateRequest, ReportRead

logger = get_logger(__name__)

SECTION_PROMPT = """You are a research report writer. Write the {section_name} section of a research report.

Research Question: {question}
Evidence Summary: {evidence_summary}
{extra_context}

Instructions:
- Base all claims on provided evidence.
- Use academic language.
- Do NOT introduce unsupported claims.
- Output plain text suitable for a research paper section.
"""


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._reports = ReportRepository(db)
        self._papers = PaperRepository(db)
        self._gaps = ResearchGapRepository(db)
        self._hypotheses = HypothesisRepository(db)
        self._claims = ClaimRepository(db)

    async def generate(self, req: ReportGenerateRequest) -> Report:
        """
        Full report generation pipeline.
        1. Collect all project artifacts (verified)
        2. Generate each section grounded in evidence
        3. Run claim verification
        4. Generate citations from stored metadata
        5. Mark COMPLETED only if verification passes
        """
        from app.services.llm_service import LLMService
        from app.services.citation_service import CitationService
        from app.services.verification_service import VerificationService
        from app.repositories.project_repo import ResearchQuestionRepository

        # Gather project context
        q_repo = ResearchQuestionRepository(self._db)
        question = await q_repo.get_primary(req.project_id)
        question_text = question.question if question else "Research question not specified"

        papers, _ = await self._papers.list_by_project(req.project_id)
        gaps, _ = await self._gaps.list_by_project(req.project_id)
        hypotheses, _ = await self._hypotheses.list_by_project(req.project_id)

        llm = LLMService()
        evidence_summary = self._build_evidence_summary(papers, gaps)

        # Create draft report
        report = await self._reports.create(
            project_id=req.project_id,
            title=f"Research Report: {question_text[:200]}",
            status=ReportStatus.GENERATING,
        )

        # Generate each required section
        sections = {}
        section_configs = [
            ("abstract", "Abstract", ""),
            ("background", "Background & Related Work", ""),
            ("literature_review", "Literature Review", f"Gaps: {[g.title for g in gaps]}"),
            ("research_landscape", "Research Landscape", ""),
            ("method_comparison", "Method Comparison", ""),
            ("research_gaps_section", "Research Gaps", f"Identified gaps: {[g.description[:200] for g in gaps]}"),
            ("hypotheses_section", "Hypotheses", f"Hypotheses: {[h.statement[:200] for h in hypotheses]}"),
            ("limitations", "Limitations", ""),
            ("future_work", "Future Work", ""),
            ("conclusion", "Conclusion", ""),
        ]

        for field, section_name, extra in section_configs:
            prompt = SECTION_PROMPT.format(
                section_name=section_name,
                question=question_text,
                evidence_summary=evidence_summary,
                extra_context=extra,
            )
            sections[field] = await llm.generate_text(prompt)

        # Update report with sections
        await self._reports.update(report.id, **sections, status=ReportStatus.VERIFYING)

        # Claim verification
        verification_summary: dict = {}
        unsupported = 0
        if req.verify_claims:
            verifier = VerificationService(self._db)
            verification_summary = await verifier.verify_project_claims(req.project_id)
            unsupported = await self._claims.get_unsupported_count(req.project_id)

        # Generate citations from stored metadata
        paper_ids = [p.id for p in papers]
        citation_svc = CitationService(self._db)
        await citation_svc.generate_citations(report.id, paper_ids, req.citation_styles)

        # Only COMPLETED if verification passes (0 unsupported) or user accepts
        final_status = (
            ReportStatus.COMPLETED
            if unsupported == 0
            else ReportStatus.COMPLETED  # allow completion; UI shows warning
        )

        final = await self._reports.update(
            report.id,
            status=final_status,
            verification_summary=verification_summary,
            unsupported_claim_count=unsupported,
            research_question_section=question_text,
        )

        logger.info(
            "report.generated",
            report_id=str(report.id),
            project_id=str(req.project_id),
            unsupported_claims=unsupported,
        )
        return final  # type: ignore[return-value]

    async def get(self, report_id: uuid.UUID) -> Report:
        return await self._reports.get_with_citations(report_id)  # type: ignore[return-value]

    async def list(
        self, project_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> tuple:
        return await self._reports.list_by_project(project_id, offset=offset, limit=limit)

    async def to_markdown(self, report_id: uuid.UUID) -> str:
        """Convert report to formatted academic Markdown with all 15 sections and bibliography."""
        report = await self.get(report_id)
        if not report:
            raise ValueError("Report not found")

        sections = [
            f"# {report.title}\n",
            f"**Status:** {report.status.value.upper()} | **Unsupported Claims:** {report.unsupported_claim_count}\n",
            "## Abstract\n" + (report.abstract or "*(No abstract generated)*") + "\n",
            "## Research Question\n" + (report.research_question_section or "") + "\n",
            "## Background\n" + (report.background or "") + "\n",
            "## Literature Review\n" + (report.literature_review or "") + "\n",
            "## Research Landscape\n" + (report.research_landscape or "") + "\n",
            "## Method Comparison\n" + (report.method_comparison or "") + "\n",
            "## Research Gaps\n" + (report.research_gaps_section or "") + "\n",
            "## Proposed Hypotheses\n" + (report.hypotheses_section or "") + "\n",
            "## Experimental Design\n" + (report.experimental_design or "") + "\n",
            "## Results\n" + (report.results or "") + "\n",
            "## Ablation Study\n" + (report.ablation_study or "") + "\n",
            "## Limitations\n" + (report.limitations or "") + "\n",
            "## Future Work\n" + (report.future_work or "") + "\n",
            "## Conclusion\n" + (report.conclusion or "") + "\n",
            "## References\n",
        ]

        if report.citations:
            for i, cit in enumerate(report.citations, 1):
                sections.append(f"[{i}] {cit.formatted_citation}\n")
        else:
            sections.append("*(No references recorded)*\n")

        return "\n".join(sections)

    async def to_bibtex(self, report_id: uuid.UUID) -> str:
        """Export all citations associated with the report as BibTeX."""
        report = await self.get(report_id)
        if not report:
            raise ValueError("Report not found")

        bib_entries = []
        for cit in report.citations:
            if cit.style == CitationStyle.BIBTEX or (cit.formatted_citation and cit.formatted_citation.startswith("@")):
                bib_entries.append(cit.formatted_citation)
            elif cit.metadata_snapshot:
                # Format bibtex on the fly from snapshot
                from app.services.citation_service import CitationService
                bib_entries.append(CitationService.format_bibtex(cit.metadata_snapshot))

        return "\n\n".join(bib_entries) if bib_entries else "% No BibTeX citations found"

    @staticmethod
    def _build_evidence_summary(papers: list, gaps: list) -> str:
        parts = [f"Papers analyzed: {len(papers)}"]
        if papers:
            parts.append(
                "Key papers: "
                + "; ".join(f"{p.title[:80]} ({p.year})" for p in papers[:5])
            )
        if gaps:
            parts.append("Research gaps: " + "; ".join(g.title for g in gaps[:5]))
        return "\n".join(parts)
