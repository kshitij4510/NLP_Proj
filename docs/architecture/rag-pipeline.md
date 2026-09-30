# RAG Pipeline Architecture

## Hybrid Retrieval Pipeline

```mermaid
flowchart LR
    Q[Query] --> BM25[BM25 Sparse\nrank-bm25]
    Q --> EMBED[Query Embedding\nBGE-small]
    EMBED --> DENSE[Dense Retrieval\npgvector cosine]
    BM25 --> MERGE[Candidate Merge\nRRF Fusion]
    DENSE --> MERGE
    MERGE --> FILTER[Metadata Filter\nyear · venue · source]
    FILTER --> FUSION[Score Fusion\nα·dense + β·BM25]
    FUSION --> RERANK[Cross-Encoder Rerank\nms-marco-MiniLM-L6]
    RERANK --> EVIDENCE[Evidence Snippets\nwith full provenance]

    style Q fill:#dbeafe
    style EVIDENCE fill:#d1fae5
```

## Evidence Snippet Structure

Every retrieved snippet exposes:

| Field | Description |
|---|---|
| `chunk_id` | Unique chunk identifier |
| `paper_id` | Source paper |
| `paper_title` | Paper title |
| `authors` | Author list |
| `year` | Publication year |
| `doi` | DOI for citation |
| `content` | Exact text excerpt |
| `page_number` | Page in original PDF |
| `section_title` | Section header |
| `dense_score` | Cosine similarity (0–1) |
| `bm25_score` | Normalized BM25 score (0–1) |
| `final_score` | Post-RRF + rerank score |

## Score Fusion: Reciprocal Rank Fusion

```
RRF(chunk) = α × (1 / (k + dense_rank + 1))
           + β × (1 / (k + bm25_rank + 1))

where k = 60 (standard RRF constant)
      α = dense_weight (default 0.5)
      β = bm25_weight  (default 0.5)
```

## Synthesis Safety Invariant

```mermaid
graph LR
    EVIDENCE[Evidence Snippets\nArtifactType=EVIDENCE] --> LLM[LLM Generation]
    LLM --> OUTPUT[Synthesis Text\nArtifactType=INTERPRETATION]
    OUTPUT --> VERIFY[Claim Verification\nagainst stored chunks]
    VERIFY --> REPORT[Report Section\nwith verification status]

    style EVIDENCE fill:#d1fae5
    style OUTPUT fill:#fef3c7
    style VERIFY fill:#fee2e2
```

LLM output is **always** tagged `INTERPRETATION` — it **never** silently becomes `EVIDENCE`.
`EVIDENCE` can only be set when a claim maps to a stored chunk with high verification confidence.
