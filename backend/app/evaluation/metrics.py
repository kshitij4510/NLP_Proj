"""
Evaluation metrics — Precision@K, Recall@K, MRR, nDCG, F1.
All metrics are computed from real data. Never fabricated.
Spec §9 Evaluation Architecture.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set


def precision_at_k(retrieved: List[Any], relevant: Set[Any], k: int) -> float:
    """Precision@K: fraction of top-K retrieved that are relevant."""
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / k


def recall_at_k(retrieved: List[Any], relevant: Set[Any], k: int) -> float:
    """Recall@K: fraction of relevant items found in top-K."""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: List[Any], relevant: Set[Any]) -> float:
    """Mean Reciprocal Rank for a single query."""
    for i, item in enumerate(retrieved):
        if item in relevant:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved: List[Any], relevance_scores: Dict[Any, float], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain @ K.
    relevance_scores: {item_id: relevance_score}
    """
    def dcg(items: List[Any]) -> float:
        score = 0.0
        for i, item in enumerate(items[:k]):
            rel = relevance_scores.get(item, 0.0)
            score += rel / math.log2(i + 2)
        return score

    actual_dcg = dcg(retrieved)
    ideal_items = sorted(relevance_scores.keys(), key=lambda x: relevance_scores[x], reverse=True)
    ideal_dcg = dcg(ideal_items)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_retrieval_metrics(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k_values: List[int] = [1, 5, 10],
) -> Dict[str, float]:
    """Compute full retrieval metric suite for a single query."""
    results: Dict[str, float] = {}
    for k in k_values:
        results[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        results[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
    results["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
    return results


def compute_ner_metrics(
    predicted: List[tuple],  # (text, type)
    gold: List[tuple],
) -> Dict[str, float]:
    """Entity F1 for NER evaluation."""
    pred_set = set(predicted)
    gold_set = set(gold)
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return {"precision": prec, "recall": rec, "f1": f1_score(prec, rec)}


def compute_claim_verification_metrics(
    predictions: List[str],  # VerificationStatus values
    gold_labels: List[str],
) -> Dict[str, float]:
    """Accuracy, precision, recall, F1 for claim verification."""
    if not predictions or not gold_labels:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    correct = sum(p == g for p, g in zip(predictions, gold_labels))
    accuracy = correct / len(predictions)

    # Binary: SUPPORTED = positive
    tp = sum(1 for p, g in zip(predictions, gold_labels) if p == "SUPPORTED" == g)
    fp = sum(1 for p, g in zip(predictions, gold_labels) if p == "SUPPORTED" and g != "SUPPORTED")
    fn = sum(1 for p, g in zip(predictions, gold_labels) if p != "SUPPORTED" and g == "SUPPORTED")
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return {
        "accuracy": accuracy,
        "precision": prec,
        "recall": rec,
        "f1": f1_score(prec, rec),
    }
