"""Unit tests for scientific NER — no DB required."""
import pytest
from app.nlp.ner import extract_entities
from app.models.knowledge import EntityType


def test_extract_model_entities():
    text = "We fine-tune BERT and compare with GPT-4 on the SQuAD benchmark."
    entities = extract_entities(text)
    names = {e.name.upper() for e in entities}
    types = {e.entity_type for e in entities}
    assert EntityType.MODEL in types or EntityType.DATASET in types


def test_extract_dataset():
    text = "We evaluate on SQuAD 2.0 and the GLUE benchmark suite."
    entities = extract_entities(text)
    types = {e.entity_type for e in entities}
    assert EntityType.DATASET in types or EntityType.BENCHMARK in types


def test_entities_have_provenance():
    text = "BERT achieves state-of-the-art results on GLUE."
    entities = extract_entities(text)
    for ent in entities:
        assert ent.start_char >= 0
        assert ent.end_char > ent.start_char
        assert ent.context_snippet
        assert ent.confidence > 0.0


def test_empty_text():
    assert extract_entities("") == []


def test_no_entities():
    text = "The weather is nice today and the sun is shining brightly."
    entities = extract_entities(text)
    # May return 0 or a few entities — should not raise
    assert isinstance(entities, list)
