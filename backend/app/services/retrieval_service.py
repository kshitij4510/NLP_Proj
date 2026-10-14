"""
Retrieval service — orchestrates the hybrid BM25 + dense retrieval pipeline.
Delegates to retrieval/ modules; owns query routing and result assembly.
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.schemas.paper import EvidenceSnippet
from app.schemas.retrieval import RetrievalQuery, RetrievalResult

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """
        Full hybrid retrieval pipeline (spec §3 Retrieval Layer):
        Query → BM25 → Dense → Merge → Filter → Score Fusion → Rerank → Evidence
        """
        from app.retrieval.hybrid import HybridRetriever

        t0 = time.monotonic()
        retriever = HybridRetriever(self._db)

        evidence, stats = await retriever.search(
            query=query.query,
            project_id=query.project_id,
            top_k=query.top_k,
            use_reranking=query.use_reranking,
            metadata_filters=query.metadata_filters,
            year_min=query.year_min,
            year_max=query.year_max,
            bm25_weight=query.bm25_weight,
            dense_weight=query.dense_weight,
        )

        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "retrieval.complete",
            project_id=str(query.project_id),
            query_len=len(query.query),
            results=len(evidence),
            elapsed_ms=round(elapsed_ms, 1),
        )

        return RetrievalResult(
            query=query.query,
            evidence=evidence,
            total_candidates=stats.get("total_candidates", 0),
            retrieval_time_ms=elapsed_ms,
            bm25_candidates=stats.get("bm25_candidates", 0),
            dense_candidates=stats.get("dense_candidates", 0),
            reranked=bool(stats.get("reranked", False)),
        )
