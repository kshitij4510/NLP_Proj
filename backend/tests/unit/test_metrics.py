"""Unit tests for evaluation metrics — real computation, never fabricated."""
import pytest
from app.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
    f1_score,
    compute_retrieval_metrics,
    compute_ner_metrics,
    compute_claim_verification_metrics,
)


def test_precision_at_k_perfect():
    retrieved = ["a", "b", "c"]
    relevant = {"a", "b", "c"}
    assert precision_at_k(retrieved, relevant, 3) == 1.0


def test_precision_at_k_none():
    retrieved = ["x", "y", "z"]
    relevant = {"a", "b"}
    assert precision_at_k(retrieved, relevant, 3) == 0.0


def test_precision_at_k_partial():
    retrieved = ["a", "x", "b"]
    relevant = {"a", "b"}
    assert precision_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)


def test_recall_at_k():
    retrieved = ["a", "b", "x", "y"]
    relevant = {"a", "b", "c"}
    assert recall_at_k(retrieved, relevant, 4) == pytest.approx(2 / 3)


def test_recall_empty_relevant():
    assert recall_at_k(["a"], set(), 1) == 0.0


def test_mrr_first_hit():
    retrieved = ["a", "b", "c"]
    relevant = {"a"}
    assert reciprocal_rank(retrieved, relevant) == 1.0


def test_mrr_second_hit():
    retrieved = ["x", "a", "b"]
    relevant = {"a"}
    assert reciprocal_rank(retrieved, relevant) == pytest.approx(0.5)


def test_mrr_no_hit():
    retrieved = ["x", "y", "z"]
    relevant = {"a"}
    assert reciprocal_rank(retrieved, relevant) == 0.0


def test_ndcg_perfect():
    retrieved = ["a", "b", "c"]
    scores = {"a": 1.0, "b": 0.8, "c": 0.6}
    assert ndcg_at_k(retrieved, scores, 3) == pytest.approx(1.0)


def test_f1_balanced():
    assert f1_score(0.8, 0.6) == pytest.approx(2 * 0.8 * 0.6 / (0.8 + 0.6))


def test_f1_zero():
    assert f1_score(0.0, 0.0) == 0.0


def test_compute_retrieval_metrics():
    metrics = compute_retrieval_metrics(
        retrieved_ids=["a", "b", "x", "c"],
        relevant_ids={"a", "b", "c"},
        k_values=[1, 3, 5],
    )
    assert "precision@1" in metrics
    assert "recall@3" in metrics
    assert "mrr" in metrics
    assert metrics["precision@1"] == 1.0
    assert metrics["mrr"] == 1.0


def test_compute_ner_metrics():
    predicted = [("BERT", "MODEL"), ("SQuAD", "DATASET")]
    gold = [("BERT", "MODEL"), ("GPT-4", "MODEL")]
    metrics = compute_ner_metrics(predicted, gold)
    assert metrics["f1"] >= 0.0
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["recall"] == pytest.approx(0.5)


def test_compute_claim_verification_metrics():
    predictions = ["SUPPORTED", "CONTRADICTED", "SUPPORTED"]
    gold = ["SUPPORTED", "SUPPORTED", "SUPPORTED"]
    metrics = compute_claim_verification_metrics(predictions, gold)
    assert metrics["accuracy"] == pytest.approx(2 / 3)
    assert "f1" in metrics
