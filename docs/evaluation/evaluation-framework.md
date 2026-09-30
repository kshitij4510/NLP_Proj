# Evaluation Framework

All metrics are computed from real data. **Never fabricated.**

## Retrieval Metrics (spec §9)

| Metric | Description | Implementation |
|---|---|---|
| Precision@K | Fraction of top-K relevant | `evaluation/metrics.py` |
| Recall@K | Fraction of relevant found | `evaluation/metrics.py` |
| MRR | Mean Reciprocal Rank | `evaluation/metrics.py` |
| nDCG@K | Normalized DCG | `evaluation/metrics.py` |

## RAG Metrics

| Metric | Description |
|---|---|
| Faithfulness | Claims grounded in retrieved chunks |
| Context relevance | Retrieved chunks relevant to query |
| Answer relevance | Synthesis addresses the question |

## Claim Verification Metrics

| Metric | Description |
|---|---|
| Accuracy | Overall correctness |
| Precision | Fraction of SUPPORTED that are truly supported |
| Recall | Fraction of true evidence found |
| F1 | Harmonic mean |

## Information Extraction Metrics

| Metric | Description |
|---|---|
| Entity F1 | Named entity precision/recall/F1 |
| Relation F1 | Relation extraction quality |

## Baseline Comparison (spec §9)

| System | BM25 | Dense | Hybrid | KG | Verification |
|---|---|---|---|---|---|
| Keyword Search | ✗ | ✗ | ✗ | ✗ | ✗ |
| BM25 | ✓ | ✗ | ✗ | ✗ | ✗ |
| Dense Retrieval | ✗ | ✓ | ✗ | ✗ | ✗ |
| Basic RAG | ✗ | ✓ | ✗ | ✗ | ✗ |
| Hybrid RAG | ✓ | ✓ | ✓ | ✗ | ✗ |
| **ResearchMind** | ✓ | ✓ | ✓ | ✓ | ✓ |

## Ablation Study (spec §9)

| Ablation | Removes |
|---|---|
| ResearchMind | — (full system) |
| − Knowledge Graph | Entity/relation extraction |
| − Hybrid Retrieval | Dense only |
| − Claim Verification | No verification step |
| − Reranking | RRF only, no cross-encoder |
| − Research Planner | Single query, no expansion |

## System Metrics

| Metric | Measured By |
|---|---|
| Latency | Request timing middleware |
| Throughput | Requests/sec at worker |
| Token usage | LLM API response metadata |
| Cost | Token count × per-token price |
| Memory | Docker container stats |
