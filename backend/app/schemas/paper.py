"""Paper-related schemas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import Field, HttpUrl, ConfigDict

from app.models.paper import PaperStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class PaperAuthorRead(BaseSchema):
    id: uuid.UUID
    name: str
    affiliation: Optional[str]
    orcid: Optional[str]
    position: int


class PaperCreate(BaseSchema):
    """Used when manually adding a paper (URL or DOI)."""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    title: Optional[str] = Field(default=None, max_length=2000)


class PaperRead(IDSchema, TimestampSchema):
    project_id: uuid.UUID
    doi: Optional[str]
    arxiv_id: Optional[str]
    title: str
    abstract: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    citation_count: int
    source: str
    status: PaperStatus
    relevance_score: Optional[float]
    authors: List[PaperAuthorRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaperSearchResult(BaseSchema):
    """Result from academic API discovery."""
    title: str
    abstract: Optional[str]
    authors: List[str]
    year: Optional[int]
    venue: Optional[str]
    doi: Optional[str]
    arxiv_id: Optional[str]
    pdf_url: Optional[str]
    citation_count: int
    source: str
    relevance_score: Optional[float]
    external_id: Optional[str]


class ChunkRead(BaseSchema):
    id: uuid.UUID
    paper_id: uuid.UUID
    content: str
    chunk_index: int
    page_number: Optional[int]


class EvidenceSnippet(BaseSchema):
    """
    Used in retrieval results — every snippet traces back to a paper/chunk.
    """
    chunk_id: uuid.UUID
    paper_id: uuid.UUID
    paper_title: str
    authors: List[str]
    year: Optional[int]
    doi: Optional[str]
    content: str
    page_number: Optional[int]
    section_title: Optional[str]
    dense_score: Optional[float]
    bm25_score: Optional[float]
    metadata_relevance: Optional[float]
    final_score: float
