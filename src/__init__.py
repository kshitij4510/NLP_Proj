"""NLP Project — source package."""

from .preprocessing import TextPreprocessor, get_word_frequencies
from .classification import TextClassifier
from .ner import spacy_ner, hf_ner

__all__ = [
    "TextPreprocessor",
    "get_word_frequencies",
    "TextClassifier",
    "spacy_ner",
    "hf_ner",
]
