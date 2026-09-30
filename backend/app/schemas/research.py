"""Research gap and hypothesis schemas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import Field

from app.models.research import GapType, HypothesisStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ResearchGapRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    title: str
    description: str
    gap_type: GapType
    importance_score: Optional[float]
    supporting_paper_ids: Optional[List[uuid.UUID]]
    detected_by: str


class HypothesisCreate(BaseSchema):
    statement: str = Field(min_length=10)
    rationale: Optional[str] = None
    gap_id: Optional[uuid.UUID] = None


class HypothesisUpdate(BaseSchema):
    statement: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[HypothesisStatus] = None


class HypothesisRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    gap_id: Optional[uuid.UUID]
    statement: str
    rationale: Optional[str]
    status: HypothesisStatus
    confidence: Optional[float]
    testability_score: Optional[float]


class ResearchPlan(BaseSchema):
    """Structured 10-field autonomous research plan (Spec Module B)."""
    research_question: str
    problem_definition: str = ""
    sub_questions: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    search_strategy: List[str] = Field(default_factory=list)
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)
    candidate_datasets: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    potential_experiments: List[str] = Field(default_factory=list)
    is_approved: bool = False


class ResearchPlanUpdate(BaseSchema):
    problem_definition: Optional[str] = None
    sub_questions: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    related_concepts: Optional[List[str]] = None
    search_strategy: Optional[List[str]] = None
    inclusion_criteria: Optional[List[str]] = None
    exclusion_criteria: Optional[List[str]] = None
    candidate_datasets: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    potential_experiments: Optional[List[str]] = None
    is_approved: Optional[bool] = None


class TemporalPoint(BaseSchema):
    year: int
    paper_count: int
    top_models: List[str] = Field(default_factory=list)
    top_datasets: List[str] = Field(default_factory=list)
    top_topics: List[str] = Field(default_factory=list)


class TemporalAnalysisRead(BaseSchema):
    project_id: uuid.UUID
    timeline: List[TemporalPoint]
    model_evolution: List[dict] = Field(default_factory=list)
    dataset_popularity: List[dict] = Field(default_factory=list)
    topic_trends: List[dict] = Field(default_factory=list)
