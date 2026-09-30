"""
Dense vector retrieval using pgvector cosine similarity.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.nlp.embeddings import get_embedding_engine
from app.repositories.paper_repo import PaperChunkRepository

logger = get_logger(__name__)


class DenseRetriever:
    """
    Project-scoped dense retriever using pgvector.
    Query → embedding → cosine search over paper_chunks.
    """

    def __init__(self, db) -> None:
        self._db = db
        self._engine = get_embedding_engine()

    async def search(
        self,
        query: str,
        project_id: uuid.UUID,
        top_k: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[Tuple[uuid.UUID, float]]:
        """
        Returns list of (chunk_id, cosine_similarity) sorted descending.
        """
        query_embedding = await self._engine.encode_query(query)

        chunk_repo = PaperChunkRepository(self._db)
        results = await chunk_repo.vector_search(
            project_id=project_id,
            query_embedding=query_embedding,
            top_k=top_k,
            year_min=year_min,
            year_max=year_max,
        )

        # results is list of (PaperChunk, similarity_score)
        return [(chunk.id, score) for chunk, score in results]
