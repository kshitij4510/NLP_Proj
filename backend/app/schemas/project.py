"""Project and research question schemas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import Field

from app.models.project import ProjectStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ResearchQuestionCreate(BaseSchema):
    question: str = Field(min_length=10, max_length=2000)
    sub_questions: Optional[List[str]] = Field(default_factory=list)
    scope: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    is_primary: bool = True


class ResearchQuestionRead(IDSchema):
    project_id: uuid.UUID
    question: str
    sub_questions: Optional[List[str]]
    scope: Optional[str]
    keywords: Optional[List[str]]
    is_primary: bool


class ProjectCreate(BaseSchema):
    title: str = Field(min_length=3, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    research_question: Optional[ResearchQuestionCreate] = None


class ProjectUpdate(BaseSchema):
    title: Optional[str] = Field(default=None, min_length=3, max_length=500)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[List[str]] = None


class ProjectRead(IDSchema, TimestampSchema):
    owner_id: uuid.UUID
    title: str
    description: Optional[str]
    status: ProjectStatus
    tags: Optional[List[str]]


class ProjectDetail(ProjectRead):
    research_questions: List[ResearchQuestionRead] = Field(default_factory=list)
    paper_count: int = 0
    hypothesis_count: int = 0
    experiment_count: int = 0
