"""
Named Entity Recognition for scientific text.
Extracts entities of types defined in spec §3 NLP Layer:
  MODEL | DATASET | TASK | METRIC | METHOD | BENCHMARK | ORGANIZATION

Uses spaCy as base + rule-based patterns for scientific domains.
Every extracted entity retains provenance (start_char, end_char, context_snippet).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.models.knowledge import EntityType

logger = get_logger(__name__)

# ── Scientific entity patterns ─────────────────────────────────────────────────
# Pattern: (regex, EntityType, confidence_boost)
_PATTERNS: List[tuple] = [
    # Models
    (r"\b(BERT|GPT-[234]?|RoBERTa|DeBERTa|LLaMA[-\s]?\d*|T5|BART|XLNet|ALBERT|DistilBERT|GPT-4o?|Gemini[-\s]?\S*|Claude[-\s]?\S*|PaLM[-\s]?\S*)\b", EntityType.MODEL, 0.1),
    # Datasets
    (r"\b(SQuAD[-\s]?\d*|GLUE|SuperGLUE|ImageNet|COCO|WMT[-\s]?\d{4}|CoNLL[-\s]?\d{4}|BooksCorpus|WikiText[-\s]?\d*|MNLI|SST[-\s]?\d?|MultiNLI|HellaSwag|ARC[-\s]?[CE]?|TruthfulQA|MMLU|HumanEval|GSM8K)\b", EntityType.DATASET, 0.1),
    # Metrics
    (r"\b(BLEU|ROUGE[-\s]?\w?|F1|accuracy|precision|recall|perplexity|METEOR|BERTScore|MRR|nDCG|MAP|AUC[-\s]?ROC?|mAP|WER|CER|MAUVE)\b", EntityType.METRIC, 0.05),
    # Tasks
    (r"\b(machine\stranslation|text\sclassification|named\sentity\srecognition|question\sanswering|summarization|sentiment\sanalysis|natural\slanguage\sinference|coreference\sresolution|relation\sextraction|text\sgeneration|dialogue\ssystems?|reading\scomprehension)\b", EntityType.TASK, 0.0),
    # Methods
    (r"\b(transformer|attention\smechanism|self-attention|cross-attention|fine-tuning|pre-training|transfer\slearning|retrieval[-\s]augmented|RLHF|chain[-\s]of[-\s]thought|in-context\slearning|few-shot\slearning|zero-shot|prompt\stuning|LoRA|QLoRA|adapter\stuning)\b", EntityType.METHOD, 0.0),
    # Benchmarks
    (r"\b(HELM|BIG-Bench|OpenLLM\sLeaderboard|LMSYS\sChatbot\sArena|AlpacaEval|MT-Bench|HumanEval|MBPP|APPS|CodeContests)\b", EntityType.BENCHMARK, 0.1),
    # Organizations
    (r"\b(OpenAI|Google|DeepMind|Meta\sAI|Anthropic|Hugging\sFace|Microsoft\sResearch|Stanford|MIT|CMU|Berkeley|NVIDIA|Amazon\sAWS|EleutherAI|Mistral\sAI)\b", EntityType.ORGANIZATION, 0.05),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), t, b) for p, t, b in _PATTERNS]


@dataclass
class ExtractedEntity:
    name: str
    entity_type: EntityType
    confidence: float
    start_char: int
    end_char: int
    context_snippet: str


class ScientificNER:
    """
    Two-stage NER:
    1. Rule-based patterns for high-precision scientific entities
    2. spaCy for general NER (ORG, PRODUCT, etc.) as fallback
    """

    def __init__(self) -> None:
        self._nlp = None

    def _load_spacy(self) -> None:
        if self._nlp is not None:
            return
        try:
            import spacy
            from app.core.config import settings
            self._nlp = spacy.load(settings.SPACY_MODEL)
            logger.info("ner.spacy_loaded")
        except Exception as exc:
            logger.warning("ner.spacy_load_failed", error=str(exc))
            self._nlp = None

    def extract(self, text: str, chunk_id: str = "") -> List[ExtractedEntity]:
        """
        Extract all scientific entities from a text span.
        Every entity retains char offsets for provenance.
        """
        entities: Dict[str, ExtractedEntity] = {}

        # Stage 1 — rule-based patterns
        for pattern, etype, boost in _COMPILED:
            for match in pattern.finditer(text):
                name = match.group(0)
                canonical = name.strip().lower()
                start, end = match.start(), match.end()
                snippet = text[max(0, start - 50): end + 50].strip()

                if canonical not in entities or entities[canonical].confidence < 0.8 + boost:
                    entities[canonical] = ExtractedEntity(
                        name=name.strip(),
                        entity_type=etype,
                        confidence=min(1.0, 0.8 + boost),
                        start_char=start,
                        end_char=end,
                        context_snippet=snippet,
                    )

        # Stage 2 — spaCy general NER for organizations not caught by patterns
        self._load_spacy()
        if self._nlp and len(text) < 50000:
            doc = self._nlp(text[:10000])  # cap for performance
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT"):
                    canonical = ent.text.lower()
                    if canonical not in entities:
                        snippet = text[max(0, ent.start_char - 50): ent.end_char + 50].strip()
                        entities[canonical] = ExtractedEntity(
                            name=ent.text,
                            entity_type=EntityType.ORGANIZATION,
                            confidence=0.6,
                            start_char=ent.start_char,
                            end_char=ent.end_char,
                            context_snippet=snippet,
                        )

        return list(entities.values())


# Module-level singleton
_ner = ScientificNER()


def extract_entities(text: str, chunk_id: str = "") -> List[ExtractedEntity]:
    return _ner.extract(text, chunk_id)
