"""
Text Classification Module
Demonstrates sentiment analysis and multi-class text classification
using TF-IDF + Logistic Regression (sklearn) and a HuggingFace pipeline.
"""

import logging
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ── sklearn TF-IDF classifier ─────────────────────────────────────────────────

class TextClassifier:
    """TF-IDF + Logistic Regression text classifier."""

    def __init__(self, max_features: int = 10_000, C: float = 1.0):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(C=C, max_iter=1000, random_state=42)),
        ])
        self.classes_: List[str] = []

    def fit(self, texts: List[str], labels: List[str]) -> "TextClassifier":
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.classes_)
        logger.info("Classifier trained on %d samples, %d classes.", len(texts), len(self.classes_))
        return self

    def predict(self, texts: List[str]) -> np.ndarray:
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        return self.pipeline.predict_proba(texts)

    def evaluate(self, texts: List[str], labels: List[str]) -> dict:
        preds = self.predict(texts)
        report = classification_report(labels, preds, output_dict=True)
        cm = confusion_matrix(labels, preds, labels=self.classes_)
        print("\nClassification Report:")
        print(classification_report(labels, preds))
        print("Confusion Matrix:")
        print(cm)
        return {"report": report, "confusion_matrix": cm}


def train_sentiment_demo() -> TextClassifier:
    """Train a simple sentiment classifier on a toy dataset."""
    texts = [
        "I love this product, it's amazing!",
        "Absolutely fantastic experience, highly recommend.",
        "Great quality and fast shipping.",
        "Best purchase I've made this year.",
        "Wonderful service and friendly staff.",
        "Terrible product, broke after one day.",
        "Very disappointed, would not buy again.",
        "Awful quality, complete waste of money.",
        "Worst experience ever, stay away.",
        "Poor customer service and bad quality.",
        "It's okay, nothing special.",
        "Average product, meets basic expectations.",
        "Not bad, but not great either.",
        "Decent for the price, but could be better.",
        "Pretty average overall.",
    ]
    labels = (
        ["positive"] * 5
        + ["negative"] * 5
        + ["neutral"] * 5
    )

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.3, random_state=42, stratify=labels
    )

    clf = TextClassifier()
    clf.fit(X_train, y_train)
    clf.evaluate(X_test, y_test)
    return clf


# ── HuggingFace zero-shot / sentiment pipeline ────────────────────────────────

def hf_sentiment_analysis(texts: List[str]) -> List[dict]:
    """
    Run sentiment analysis using a pre-trained HuggingFace model.
    Requires: pip install transformers torch
    """
    try:
        from transformers import pipeline as hf_pipeline
        analyzer = hf_pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
        return analyzer(texts)
    except ImportError:
        logger.warning("transformers not installed. Run: pip install transformers torch")
        return []


def hf_zero_shot(texts: List[str], candidate_labels: List[str]) -> List[dict]:
    """
    Zero-shot text classification using a pre-trained HuggingFace model.
    No training data required.
    """
    try:
        from transformers import pipeline as hf_pipeline
        classifier = hf_pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        return [classifier(text, candidate_labels) for text in texts]
    except ImportError:
        logger.warning("transformers not installed. Run: pip install transformers torch")
        return []


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Text Classification Demo")
    print("=" * 60)

    print("\n[1] Training TF-IDF Sentiment Classifier...")
    clf = train_sentiment_demo()

    new_texts = [
        "This is the best thing I've ever bought!",
        "Total garbage, never buying again.",
        "It works fine, nothing to complain about.",
    ]
    preds = clf.predict(new_texts)
    probs = clf.predict_proba(new_texts)

    print("\nPredictions on new texts:")
    for text, pred, prob in zip(new_texts, preds, probs):
        confidence = max(prob)
        print(f"  '{text}'")
        print(f"  → {pred} (confidence: {confidence:.2%})\n")

    print("\n[2] HuggingFace Sentiment Analysis (requires transformers):")
    results = hf_sentiment_analysis(new_texts)
    if results:
        for text, res in zip(new_texts, results):
            print(f"  '{text}' → {res['label']} ({res['score']:.2%})")
