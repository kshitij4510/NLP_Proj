"""ResearchMind evaluation layer — computes real metrics, never fabricated."""
from app.evaluation.metrics import (
    precision_at_k, recall_at_k, reciprocal_rank, ndcg_at_k,
    f1_score, compute_retrieval_metrics, compute_ner_metrics,
    compute_claim_verification_metrics,
)
