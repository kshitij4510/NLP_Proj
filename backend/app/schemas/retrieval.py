"""Retrieval and query schemas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.paper import EvidenceSnippet


class RetrievalQuery(BaseSchema):
    query: str = Field(min_length=3, max_length=2000)
    project_id: uuid.UUID
    top_k: int = Field(default=10, ge=1, le=50)
    use_reranking: bool = True
    metadata_filters: Optional[dict] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    bm25_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    dense_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RetrievalResult(BaseSchema):
    query: str
    evidence: List[EvidenceSnippet]
    total_candidates: int
    retrieval_time_ms: float
    bm25_candidates: int
    dense_candidates: int
    reranked: bool
