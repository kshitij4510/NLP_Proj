"""
Re-ranking module.
Cross-encoder reranking for top-K candidates.
Falls back to weighted score fusion if model unavailable.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class CrossEncoderReranker:
    """
    Cross-encoder reranker using sentence-transformers cross-encoder.
    Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, effective).
    Falls back gracefully if model not available.
    """

    _instance: Optional["CrossEncoderReranker"] = None
    _model = None
    _MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    @classmethod
    def get(cls) -> "CrossEncoderReranker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        from app.core.config import settings
        if settings.EMBEDDING_MODEL == "lexical-hash" or self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._MODEL_NAME)
            logger.info("reranker.model_loaded", model=self._MODEL_NAME)
        except Exception as exc:
            logger.warning("reranker.load_failed", error=str(exc))
            self._model = None

    def rerank_sync(
        self, query: str, passages: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        Rerank (passage_text, fusion_score) pairs.
        Returns list sorted by rerank score descending.
        """
        if not passages:
            return passages

        self._load()
        if self._model is None:
            # No cross-encoder available — return as-is
            return sorted(passages, key=lambda x: x[1], reverse=True)

        texts = [p[0] for p in passages]
        try:
            pairs = [[query, t] for t in texts]
            scores = self._model.predict(pairs, show_progress_bar=False)
            reranked = sorted(
                zip(texts, scores.tolist()),
                key=lambda x: x[1],
                reverse=True,
            )
            return reranked
        except Exception as exc:
            logger.warning("reranker.predict_failed", error=str(exc))
            return sorted(passages, key=lambda x: x[1], reverse=True)

    async def rerank(
        self, query: str, passages: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.rerank_sync(query, passages)
        )
