"""
Named Entity Recognition (NER) Module
Demonstrates NER using spaCy and HuggingFace Transformers.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


# ── spaCy NER ─────────────────────────────────────────────────────────────────

def spacy_ner(texts: List[str], model: str = "en_core_web_sm") -> List[List[Dict]]:
    """
    Extract named entities using spaCy.

    Args:
        texts: List of input strings.
        model: spaCy model name. Download with:
               python -m spacy download en_core_web_sm

    Returns:
        List of entity lists. Each entity is a dict with
        keys: text, label, start_char, end_char.
    """
    try:
        import spacy
        nlp = spacy.load(model)
    except OSError:
        logger.error(
            "spaCy model '%s' not found. Run: python -m spacy download %s",
            model, model,
        )
        return [[] for _ in texts]
    except ImportError:
        logger.error("spaCy not installed. Run: pip install spacy")
        return [[] for _ in texts]

    results = []
    for doc in nlp.pipe(texts):
        entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "description": spacy.explain(ent.label_) or ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
            }
            for ent in doc.ents
        ]
        results.append(entities)
    return results


def spacy_ner_summary(texts: List[str], model: str = "en_core_web_sm") -> Dict[str, List[str]]:
    """
    Return a grouped summary of entities by label.
    """
    all_results = spacy_ner(texts, model)
    summary: Dict[str, List[str]] = {}
    for entities in all_results:
        for ent in entities:
            summary.setdefault(ent["label"], [])
            if ent["text"] not in summary[ent["label"]]:
                summary[ent["label"]].append(ent["text"])
    return summary


# ── HuggingFace NER ───────────────────────────────────────────────────────────

def hf_ner(texts: List[str]) -> List[List[Dict]]:
    """
    Extract named entities using a pre-trained HuggingFace NER model.
    Requires: pip install transformers torch
    """
    try:
        from transformers import pipeline as hf_pipeline
        ner = hf_pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple",
        )
        return [ner(text) for text in texts]
    except ImportError:
        logger.warning("transformers not installed. Run: pip install transformers torch")
        return [[] for _ in texts]


# ── Utilities ─────────────────────────────────────────────────────────────────

def highlight_entities(text: str, entities: List[Dict]) -> str:
    """
    Return the text with entity spans wrapped in [ENTITY/LABEL] notation.
    Entities must be sorted by start_char.
    """
    entities = sorted(entities, key=lambda e: e["start_char"])
    result = []
    cursor = 0
    for ent in entities:
        result.append(text[cursor:ent["start_char"]])
        result.append(f"[{ent['text']}/{ent['label']}]")
        cursor = ent["end_char"]
    result.append(text[cursor:])
    return "".join(result)


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_texts = [
        "Apple Inc. was founded by Steve Jobs and Steve Wozniak in Cupertino, California in 1976.",
        "The United Nations headquarters is located in New York City.",
        "Elon Musk, CEO of Tesla and SpaceX, announced a new initiative last Tuesday.",
        "The Eiffel Tower in Paris, France attracts millions of tourists every year.",
    ]

    print("=" * 60)
    print("Named Entity Recognition Demo")
    print("=" * 60)

    print("\n[1] spaCy NER:")
    results = spacy_ner(sample_texts)
    for text, entities in zip(sample_texts, results):
        if entities:
            highlighted = highlight_entities(text, entities)
            print(f"\n  Input    : {text}")
            print(f"  Entities : {highlighted}")
            for ent in entities:
                print(f"    - {ent['text']:<25} {ent['label']:<10} ({ent['description']})")

    print("\n[2] Entity summary by label:")
    summary = spacy_ner_summary(sample_texts)
    for label, values in summary.items():
        print(f"  {label}: {', '.join(values)}")

    print("\n[3] HuggingFace NER (requires transformers):")
    hf_results = hf_ner(sample_texts[:2])
    if hf_results and any(hf_results):
        for text, entities in zip(sample_texts[:2], hf_results):
            print(f"\n  '{text}'")
            for ent in entities:
                print(f"    - {ent.get('word', ''):<25} {ent.get('entity_group', '')}")
