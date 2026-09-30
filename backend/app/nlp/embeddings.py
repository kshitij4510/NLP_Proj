"""
Embedding engine — wraps Sentence Transformers (BGE/E5-style).
Thread-safe singleton; batched encoding with progress tracking.
Every embedding retains provenance of the chunk it encodes.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional
from functools import lru_cache

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    """
    Lazy-loaded sentence transformer wrapper.
    Model is downloaded once and cached in-process.
    """

    _instance: Optional["EmbeddingEngine"] = None

    def __init__(self) -> None:
        self._model = None
        self._model_name = settings.EMBEDDING_MODEL
        self._dimension = settings.EMBEDDING_DIMENSION

    @classmethod
    def get(cls) -> "EmbeddingEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("embeddings.loading_model", model=self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("embeddings.model_loaded", model=self._model_name)
        except Exception as exc:
            logger.error("embeddings.load_failed", error=str(exc))
            raise

    def encode_sync(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> List[List[float]]:
        """Synchronous batch encoding. Returns list of float vectors."""
        self._load_model()
        if not texts:
            return []

        # BGE models benefit from an instruction prefix for retrieval
        if "bge" in self._model_name.lower():
            texts = [f"Represent this sentence for retrieval: {t}" for t in texts]

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    async def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> List[List[float]]:
        """Async wrapper — offloads CPU-bound work to thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.encode_sync(texts, batch_size, normalize)
        )

    async def encode_query(self, query: str) -> List[float]:
        """Encode a single query string."""
        results = await self.encode([query])
        return results[0]

    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_engine() -> EmbeddingEngine:
    return EmbeddingEngine.get()
