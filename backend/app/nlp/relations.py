"""
Scientific relation extraction.
Extracts relations defined in spec §3 NLP Layer:
  evaluated_on | achieves | improves | compared_with | cites |
  used_for | supports | contradicts | based_on

Uses pattern matching + optional transformer-based inference.
Every relation retains evidence provenance (paper_id, chunk_id, snippet).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.logging import get_logger
from app.models.knowledge import RelationType
from app.nlp.ner import ExtractedEntity

logger = get_logger(__name__)

# ── Relation trigger patterns ──────────────────────────────────────────────────
# (trigger_regex, RelationType, confidence)
_RELATION_PATTERNS: List[Tuple[str, RelationType, float]] = [
    (r"evaluated?\s+on|tested?\s+on|assessed?\s+on|benchmarked?\s+on", RelationType.EVALUATED_ON, 0.85),
    (r"achieves?\s+(?:state[-\s]of[-\s]the[-\s]art|SOTA|best|highest|top)\s+(?:results?|performance|score)", RelationType.ACHIEVES, 0.9),
    (r"outperforms?|surpasses?|improves?\s+(?:upon|over)|better\s+than|superior\s+to", RelationType.IMPROVES, 0.85),
    (r"compared?\s+(?:with|against|to)|comparison\s+with|vs\.?|versus", RelationType.COMPARED_WITH, 0.8),
    (r"proposed?\s+by|introduced?\s+by|presented?\s+in|based\s+on\s+the\s+work", RelationType.CITES, 0.75),
    (r"used?\s+for|applied?\s+to|employed?\s+for|utilized?\s+for", RelationType.USED_FOR, 0.8),
    (r"supports?|confirms?|validates?|consistent\s+with|in\s+line\s+with", RelationType.SUPPORTS, 0.75),
    (r"contradicts?|inconsistent\s+with|in\s+contrast\s+to|contrary\s+to|conflicts?\s+with", RelationType.CONTRADICTS, 0.85),
    (r"based\s+on|builds?\s+on|extends?|derived?\s+from|inspired?\s+by", RelationType.BASED_ON, 0.8),
]

_COMPILED_RELATIONS = [
    (re.compile(p, re.IGNORECASE), rel_type, conf)
    for p, rel_type, conf in _RELATION_PATTERNS
]


@dataclass
class ExtractedRelation:
    source_name: str
    target_name: str
    relation_type: RelationType
    confidence: float
    evidence_snippet: str
    source_entity_type: Optional[str] = None
    target_entity_type: Optional[str] = None


def extract_relations(
    text: str,
    entities: List[ExtractedEntity],
    window_chars: int = 200,
) -> List[ExtractedRelation]:
    """
    Extract relations between entities in a text chunk.
    Uses a sentence-window approach: for each trigger found,
    look for entity pairs within `window_chars` characters.

    Every returned relation includes an evidence snippet for traceability.
    """
    if len(entities) < 2:
        return []

    relations: List[ExtractedRelation] = []

    for pattern, rel_type, base_confidence in _COMPILED_RELATIONS:
        for trigger_match in pattern.finditer(text):
            t_start, t_end = trigger_match.start(), trigger_match.end()

            # Find entities within window of the trigger
            window_start = max(0, t_start - window_chars)
            window_end = min(len(text), t_end + window_chars)
            snippet = text[window_start:window_end].strip()

            nearby = [
                e for e in entities
                if window_start <= e.start_char <= window_end
                or window_start <= e.end_char <= window_end
            ]

            if len(nearby) < 2:
                continue

            # Pair the closest entities around the trigger
            left_entities = [e for e in nearby if e.end_char <= t_start]
            right_entities = [e for e in nearby if e.start_char >= t_end]

            source = max(left_entities, key=lambda e: e.end_char, default=None)
            target = min(right_entities, key=lambda e: e.start_char, default=None)

            if source is None or target is None:
                # Fallback: use any two nearby entities
                if len(nearby) >= 2:
                    source, target = nearby[0], nearby[1]
                else:
                    continue

            if source.name == target.name:
                continue

            relations.append(
                ExtractedRelation(
                    source_name=source.name,
                    target_name=target.name,
                    relation_type=rel_type,
                    confidence=base_confidence * source.confidence * target.confidence,
                    evidence_snippet=snippet[:500],
                    source_entity_type=source.entity_type.value,
                    target_entity_type=target.entity_type.value,
                )
            )

    # Deduplicate
    seen: set = set()
    unique: List[ExtractedRelation] = []
    for r in relations:
        key = (r.source_name.lower(), r.target_name.lower(), r.relation_type.value)
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique
