"""
BM25 sparse retrieval over paper chunks.
Uses rank-bm25 library. Index is built per-project and cached in Redis.
"""
from __future__ import annotations

import json
import uuid
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.repositories.paper_repo import PaperChunkRepository

logger = get_logger(__name__)

_BM25_K1 = 1.5
_BM25_B = 0.75


class BM25Retriever:
    """
    Project-scoped BM25 retriever.
    Builds an in-memory index from all chunks in a project.
    """

    def __init__(self, db) -> None:
        self._db = db

    async def search(
        self,
        query: str,
        project_id: uuid.UUID,
        top_k: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[Tuple[uuid.UUID, float]]:
        """
        Returns list of (chunk_id, bm25_score) sorted descending.
        """
        from rank_bm25 import BM25Okapi
        from app.models.paper import Paper
        from sqlalchemy import and_, select
        from app.models.paper import PaperChunk

        # Load all chunks for the project
        chunk_repo = PaperChunkRepository(self._db)
        stmt = (
            select(PaperChunk.id, PaperChunk.content, Paper.year)
            .join(Paper, PaperChunk.paper_id == Paper.id)
            .where(Paper.project_id == project_id)
        )
        if year_min:
            stmt = stmt.where(Paper.year >= year_min)
        if year_max:
            stmt = stmt.where(Paper.year <= year_max)

        result = await self._db.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        chunk_ids = [row[0] for row in rows]
        corpus = [row[1] for row in rows]

        # Build BM25 index
        tokenized = [doc.lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized, k1=_BM25_K1, b=_BM25_B)

        # Score query
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Pair with chunk IDs and sort
        scored = sorted(
            zip(chunk_ids, scores.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )

        # Normalize scores to [0, 1]
        if scored:
            max_score = max(s for _, s in scored) or 1.0
            scored = [(cid, s / max_score) for cid, s in scored]

        return scored[:top_k]
