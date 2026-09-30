"""
Citation service — formats citations from stored paper metadata.
LLM is NEVER used to generate citation content (spec §3 Citation Layer).
"""
from __future__ import annotations

import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.paper import Paper
from app.models.report import Citation, CitationStyle
from app.repositories.paper_repo import PaperAuthorRepository, PaperRepository
from app.repositories.report_repo import CitationRepository

logger = get_logger(__name__)


class CitationService:
    def __init__(self, db: AsyncSession) -> None:
        self._citations = CitationRepository(db)
        self._papers = PaperRepository(db)
        self._authors = PaperAuthorRepository(db)

    async def generate_citations(
        self,
        report_id: uuid.UUID,
        paper_ids: List[uuid.UUID],
        styles: List[CitationStyle],
    ) -> List[Citation]:
        """
        Generate formatted citations for a list of papers.
        All citation data comes from stored metadata — never from an LLM.
        """
        created: List[Citation] = []
        for paper_id in paper_ids:
            paper = await self._papers.get_with_authors(paper_id)
            if not paper:
                continue
            for style in styles:
                formatted = self._format(paper, style)
                in_text = self._in_text(paper, style)
                citation = await self._citations.create(
                    report_id=report_id,
                    paper_id=paper_id,
                    style=style,
                    formatted_citation=formatted,
                    in_text_citation=in_text,
                    metadata_snapshot={
                        "title": paper.title,
                        "authors": [a.name for a in paper.authors],
                        "year": paper.year,
                        "venue": paper.venue,
                        "doi": paper.doi,
                        "arxiv_id": paper.arxiv_id,
                    },
                )
                created.append(citation)

        logger.info(
            "citations.generated",
            report_id=str(report_id),
            paper_count=len(paper_ids),
            style_count=len(styles),
        )
        return created

    # ── Format methods ───────────────────────────

    @staticmethod
    def _format(paper: Paper, style: CitationStyle) -> str:
        authors = [a.name for a in paper.authors] if paper.authors else ["Unknown"]
        year = paper.year or "n.d."
        title = paper.title
        venue = paper.venue or ""
        doi = paper.doi or ""

        if style == CitationStyle.APA:
            author_str = CitationService._apa_authors(authors)
            doi_str = f" https://doi.org/{doi}" if doi else ""
            return f"{author_str} ({year}). {title}. {venue}.{doi_str}".strip()

        if style == CitationStyle.IEEE:
            author_str = ", ".join(
                f'{a.split()[-1]}, {" ".join(a.split()[:-1])[:1]}.'
                if len(a.split()) > 1 else a
                for a in authors[:6]
            )
            if len(authors) > 6:
                author_str += " et al."
            return f'{author_str}, "{title}," {venue}, {year}.'

        if style == CitationStyle.BIBTEX:
            key = CitationService._bibtex_key(authors, year)
            author_str = " and ".join(authors)
            doi_field = f"  doi = {{{doi}}},\n" if doi else ""
            return (
                f"@article{{{key},\n"
                f"  title = {{{title}}},\n"
                f"  author = {{{author_str}}},\n"
                f"  year = {{{year}}},\n"
                f"  journal = {{{venue}}},\n"
                f"{doi_field}"
                f"}}"
            )

        return f"{authors[0]} et al. ({year}). {title}."

    @staticmethod
    def format_bibtex(meta: dict) -> str:
        """Format a BibTeX citation entry from a metadata dictionary."""
        authors = meta.get("authors") or ["Unknown"]
        year = meta.get("year") or "n.d."
        title = meta.get("title") or "Untitled"
        venue = meta.get("venue") or ""
        doi = meta.get("doi") or ""
        key = CitationService._bibtex_key(authors, year)
        author_str = " and ".join(authors) if isinstance(authors, list) else str(authors)
        doi_field = f"  doi = {{{doi}}},\n" if doi else ""
        return (
            f"@article{{{key},\n"
            f"  title = {{{title}}},\n"
            f"  author = {{{author_str}}},\n"
            f"  year = {{{year}}},\n"
            f"  journal = {{{venue}}},\n"
            f"{doi_field}"
            f"}}"
        )

    @staticmethod
    def _in_text(paper: Paper, style: CitationStyle) -> str:
        year = paper.year or "n.d."
        authors = [a.name for a in paper.authors] if paper.authors else ["Unknown"]
        first = authors[0].split()[-1] if authors[0] else "Unknown"
        suffix = " et al." if len(authors) > 2 else (f" & {authors[1].split()[-1]}" if len(authors) == 2 else "")

        if style == CitationStyle.APA:
            return f"({first}{suffix}, {year})"
        if style == CitationStyle.IEEE:
            return "[REF]"  # IEEE numbers are assigned at document level
        return f"({first}{suffix}, {year})"

    @staticmethod
    def _apa_authors(names: List[str]) -> str:
        formatted = []
        for n in names[:7]:
            parts = n.split()
            if len(parts) > 1:
                last = parts[-1]
                initials = " ".join(p[0] + "." for p in parts[:-1])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(n)
        if len(names) > 7:
            return ", ".join(formatted[:6]) + ", ... " + formatted[-1]
        if len(formatted) == 1:
            return formatted[0]
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]

    @staticmethod
    def _bibtex_key(authors: List[str], year: int | str) -> str:
        first = (authors[0].split()[-1] if authors else "unknown").lower()
        return f"{first}{year}"
