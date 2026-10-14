"""
Keyphrase extraction using KeyBERT (embedding-based).
Falls back to TF-IDF-style scoring if model unavailable.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class KeyphraseExtractor:
    """
    Extracts keyphrases from scientific text.
    Primary: KeyBERT (semantic similarity to document)
    Fallback: TF-IDF inspired n-gram scoring
    """

    def __init__(self) -> None:
        self._model = None

    def _load(self) -> None:
        from app.core.config import settings
        if settings.EMBEDDING_MODEL == "lexical-hash" or self._model is not None:
            return
        try:
            from keybert import KeyBERT
            from app.core.config import settings
            self._model = KeyBERT(model=settings.EMBEDDING_MODEL)
            logger.info("keyphrase.keybert_loaded")
        except Exception as exc:
            logger.warning("keyphrase.keybert_load_failed", error=str(exc))
            self._model = None

    def extract(
        self,
        text: str,
        top_n: int = 10,
        ngram_range: Tuple[int, int] = (1, 3),
        diversity: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """
        Extract keyphrases. Returns list of (phrase, score) tuples.
        """
        if not text.strip():
            return []

        self._load()

        if self._model is not None:
            try:
                keyphrases = self._model.extract_keywords(
                    text,
                    keyphrase_ngram_range=ngram_range,
                    stop_words="english",
                    use_maxsum=True,
                    nr_candidates=20,
                    top_n=top_n,
                    diversity=diversity,
                )
                return [(kp, float(score)) for kp, score in keyphrases]
            except Exception as exc:
                logger.warning("keyphrase.extraction_failed", error=str(exc))

        # Fallback: simple TF-IDF-style n-gram scoring
        return self._tfidf_fallback(text, top_n, ngram_range)

    @staticmethod
    def _tfidf_fallback(
        text: str, top_n: int, ngram_range: Tuple[int, int]
    ) -> List[Tuple[str, float]]:
        """Simple TF-based n-gram scoring as fallback."""
        # Tokenize
        tokens = re.findall(r'\b[a-zA-Z][a-zA-Z\-]{2,}\b', text.lower())
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "are", "was", "were",
            "this", "that", "these", "those", "we", "our", "their", "which",
        }
        tokens = [t for t in tokens if t not in stopwords]

        n_min, n_max = ngram_range
        candidates: Counter = Counter()
        for n in range(n_min, n_max + 1):
            for i in range(len(tokens) - n + 1):
                gram = " ".join(tokens[i: i + n])
                candidates[gram] += 1

        total = sum(candidates.values())
        scored = [
            (phrase, count / total)
            for phrase, count in candidates.most_common(top_n * 3)
            if count > 1
        ]
        return scored[:top_n]


# Module-level singleton
_extractor = KeyphraseExtractor()


def extract_keyphrases(
    text: str, top_n: int = 10, ngram_range: Tuple[int, int] = (1, 3)
) -> List[Tuple[str, float]]:
    return _extractor.extract(text, top_n=top_n, ngram_range=ngram_range)
