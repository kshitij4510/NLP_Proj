"""Report and citation schemas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from app.models.report import CitationStyle, ReportStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class CitationRead(BaseSchema):
    id: uuid.UUID
    paper_id: uuid.UUID
    style: CitationStyle
    formatted_citation: str
    in_text_citation: Optional[str]


class ReportRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    title: str
    status: ReportStatus
    abstract: Optional[str]
    research_question_section: Optional[str]
    background: Optional[str]
    literature_review: Optional[str]
    research_landscape: Optional[str]
    method_comparison: Optional[str]
    research_gaps_section: Optional[str]
    hypotheses_section: Optional[str]
    experimental_design: Optional[str]
    results: Optional[str]
    ablation_study: Optional[str]
    limitations: Optional[str]
    future_work: Optional[str]
    conclusion: Optional[str]
    unsupported_claim_count: int
    citations: List[CitationRead] = []


class ReportGenerateRequest(BaseSchema):
    project_id: uuid.UUID
    citation_styles: List[CitationStyle] = [CitationStyle.IEEE, CitationStyle.APA, CitationStyle.BIBTEX]
    include_ablation: bool = True
    verify_claims: bool = True
