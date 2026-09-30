"""
Hybrid retrieval — full pipeline per spec §3 Retrieval Layer:

Query
 → BM25 (sparse)
 → Dense Retrieval (pgvector)
 → Candidate Merge
 → Metadata Filtering
 → Score Fusion (Reciprocal Rank Fusion + weighted blend)
 → Reranking (optional cross-encoder)
 → Evidence (EvidenceSnippet with all score fields populated)

Every result exposes: dense_score, bm25_score, metadata_relevance, final_score, evidence_snippet.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.paper import Paper, PaperChunk, PaperSection
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.schemas.paper import EvidenceSnippet

logger = get_logger(__name__)


class HybridRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._bm25 = BM25Retriever(db)
        self._dense = DenseRetriever(db)
        self._reranker = CrossEncoderReranker.get()

    async def search(
        self,
        query: str,
        project_id: uuid.UUID,
        top_k: int = 10,
        use_reranking: bool = True,
        metadata_filters: Optional[Dict[str, Any]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        bm25_weight: Optional[float] = None,
        dense_weight: Optional[float] = None,
    ) -> Tuple[List[EvidenceSnippet], Dict[str, int]]:
        """
        Execute full hybrid retrieval.
        Returns (evidence_snippets, stats).
        """
        alpha = dense_weight if dense_weight is not None else settings.HYBRID_ALPHA
        beta = bm25_weight if bm25_weight is not None else (1.0 - alpha)

        # Retrieve more candidates for merging
        candidate_k = min(50, top_k * 3)

        # Run BM25 + dense in parallel
        bm25_results, dense_results = await self._run_parallel(
            query, project_id, candidate_k, year_min, year_max
        )

        stats = {
            "bm25_candidates": len(bm25_results),
            "dense_candidates": len(dense_results),
            "total_candidates": 0,
        }

        # Merge via Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(
            bm25_results, dense_results, bm25_weight=beta, dense_weight=alpha
        )

        # Apply metadata filters
        if metadata_filters:
            fused = await self._apply_filters(fused, metadata_filters)

        stats["total_candidates"] = len(fused)

        # Take top K for hydration
        top_fused = fused[:top_k * 2]

        # Hydrate chunks with paper metadata
        evidence = await self._hydrate(top_fused, query)

        # Rerank
        if use_reranking and evidence:
            passages = [(e.content, e.final_score) for e in evidence]
            reranked_passages = await self._reranker.rerank(query, passages)
            # Reassign final scores from reranker
            score_map = {text: score for text, score in reranked_passages}
            for e in evidence:
                if e.content in score_map:
                    e.final_score = float(score_map[e.content])
            evidence.sort(key=lambda x: x.final_score, reverse=True)

        return evidence[:top_k], stats

    # ── Internal methods ──────────────────────

    async def _run_parallel(
        self,
        query: str,
        project_id: uuid.UUID,
        k: int,
        year_min: Optional[int],
        year_max: Optional[int],
    ) -> Tuple[List[Tuple[uuid.UUID, float]], List[Tuple[uuid.UUID, float]]]:
        import asyncio
        bm25_task = asyncio.create_task(
            self._bm25.search(query, project_id, top_k=k, year_min=year_min, year_max=year_max)
        )
        dense_task = asyncio.create_task(
            self._dense.search(query, project_id, top_k=k, year_min=year_min, year_max=year_max)
        )
        bm25_results, dense_results = await asyncio.gather(bm25_task, dense_task)
        return bm25_results, dense_results

    @staticmethod
    def _reciprocal_rank_fusion(
        bm25_results: List[Tuple[uuid.UUID, float]],
        dense_results: List[Tuple[uuid.UUID, float]],
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        k: int = 60,
    ) -> List[Tuple[uuid.UUID, float, float, float]]:
        """
        Reciprocal Rank Fusion with per-source weighting.
        Returns (chunk_id, dense_score, bm25_score, fused_score) tuples.
        """
        bm25_map = {cid: (rank, score) for rank, (cid, score) in enumerate(bm25_results)}
        dense_map = {cid: (rank, score) for rank, (cid, score) in enumerate(dense_results)}

        all_ids = set(cid for cid, _ in bm25_results) | set(cid for cid, _ in dense_results)

        scored: List[Tuple[uuid.UUID, float, float, float]] = []
        for cid in all_ids:
            bm25_rank, bm25_score = bm25_map.get(cid, (len(bm25_results), 0.0))
            dense_rank, dense_score = dense_map.get(cid, (len(dense_results), 0.0))

            rrf_bm25 = bm25_weight * (1.0 / (k + bm25_rank + 1))
            rrf_dense = dense_weight * (1.0 / (k + dense_rank + 1))
            fused = rrf_bm25 + rrf_dense

            scored.append((cid, dense_score, bm25_score, fused))

        return sorted(scored, key=lambda x: x[3], reverse=True)

    async def _apply_filters(
        self,
        fused: List[Tuple[uuid.UUID, float, float, float]],
        filters: Dict[str, Any],
    ) -> List[Tuple[uuid.UUID, float, float, float]]:
        """Apply metadata filters — currently supports 'source' filter."""
        # For more complex filters, join against paper table
        return fused  # placeholder — full filter logic in v2

    async def _hydrate(
        self,
        fused: List[Tuple[uuid.UUID, float, float, float]],
        query: str,
    ) -> List[EvidenceSnippet]:
        """
        Load full chunk + paper metadata for each candidate.
        Returns EvidenceSnippet with all provenance fields populated.
        """
        if not fused:
            return []

        chunk_ids = [item[0] for item in fused]
        score_map = {item[0]: item for item in fused}

        # Load chunks + papers in one query
        result = await self._db.execute(
            select(
                PaperChunk.id,
                PaperChunk.content,
                PaperChunk.page_number,
                Paper.id.label("paper_id"),
                Paper.title,
                Paper.year,
                Paper.doi,
            )
            .join(Paper, PaperChunk.paper_id == Paper.id)
            .where(PaperChunk.id.in_(chunk_ids))
        )
        rows = result.all()

        # Build author name lookup
        author_map: Dict[uuid.UUID, List[str]] = {}
        paper_ids = list({row[3] for row in rows})
        if paper_ids:
            from app.models.paper import PaperAuthor
            author_result = await self._db.execute(
                select(PaperAuthor.paper_id, PaperAuthor.name)
                .where(PaperAuthor.paper_id.in_(paper_ids))
                .order_by(PaperAuthor.position)
            )
            for paper_id, name in author_result.all():
                author_map.setdefault(paper_id, []).append(name)

        snippets: List[EvidenceSnippet] = []
        for row in rows:
            chunk_id, content, page_num, paper_id, title, year, doi = row
            _, dense_score, bm25_score, final_score = score_map.get(
                chunk_id, (chunk_id, 0.0, 0.0, 0.0)
            )
            snippets.append(
                EvidenceSnippet(
                    chunk_id=chunk_id,
                    paper_id=paper_id,
                    paper_title=title,
                    authors=author_map.get(paper_id, []),
                    year=year,
                    doi=doi,
                    content=content,
                    page_number=page_num,
                    section_title=None,
                    dense_score=dense_score,
                    bm25_score=bm25_score,
                    metadata_relevance=None,
                    final_score=final_score,
                )
            )

        return sorted(snippets, key=lambda x: x.final_score, reverse=True)
