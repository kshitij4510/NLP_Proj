# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require:
```
Authorization: Bearer <access_token>
```

Tokens expire in 60 minutes. Use `/auth/refresh` to renew.

---

## Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get access + refresh tokens |
| POST | `/auth/refresh` | Refresh tokens |

---

## Projects

| Method | Path | Description |
|---|---|---|
| POST | `/projects` | Create project |
| GET | `/projects` | List projects (paginated) |
| GET | `/projects/{id}` | Get project detail |
| PATCH | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| POST | `/projects/{id}/questions` | Add research question |
| GET | `/projects/{id}/questions` | List research questions |

---

## Papers

| Method | Path | Description |
|---|---|---|
| POST | `/projects/{id}/papers` | Add paper by DOI/arXiv/URL |
| POST | `/projects/{id}/papers/upload` | Upload PDF file |
| GET | `/projects/{id}/papers` | List papers |
| GET | `/projects/{id}/papers/{pid}` | Get paper |
| DELETE | `/projects/{id}/papers/{pid}` | Delete paper |

---

## Retrieval

| Method | Path | Description |
|---|---|---|
| POST | `/retrieval/search` | Hybrid BM25+dense search |

### Search Request
```json
{
  "query": "transformer attention mechanism NLP",
  "project_id": "uuid",
  "top_k": 10,
  "use_reranking": true,
  "year_min": 2020,
  "year_max": 2024
}
```

### Search Response
```json
{
  "query": "...",
  "evidence": [{
    "chunk_id": "uuid",
    "paper_id": "uuid",
    "paper_title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "year": 2017,
    "doi": "10.48550/arXiv.1706.03762",
    "content": "We propose a new simple network architecture...",
    "page_number": 2,
    "section_title": "Model Architecture",
    "dense_score": 0.91,
    "bm25_score": 0.74,
    "final_score": 0.83
  }],
  "total_candidates": 47,
  "retrieval_time_ms": 142.3,
  "reranked": true
}
```

---

## Research Pipeline

| Method | Path | Description |
|---|---|---|
| POST | `/projects/{id}/research/pipeline/run` | Trigger full pipeline |
| POST | `/projects/{id}/research/synthesize` | Trigger synthesis only |
| GET | `/projects/{id}/research/summary` | Get project summary |
| GET | `/projects/{id}/research/gaps` | List research gaps |
| POST | `/projects/{id}/research/hypotheses` | Create hypothesis |
| GET | `/projects/{id}/research/hypotheses` | List hypotheses |
| POST | `/projects/{id}/research/gaps/{gid}/hypotheses/generate` | Auto-generate hypotheses |

---

## Experiments

| Method | Path | Description |
|---|---|---|
| POST | `/projects/{id}/experiments` | Create experiment spec |
| POST | `/projects/{id}/experiments/design/{hyp_id}` | Auto-design from hypothesis |
| GET | `/projects/{id}/experiments` | List experiments |
| GET | `/projects/{id}/experiments/{eid}` | Get experiment |
| POST | `/projects/{id}/experiments/{eid}/runs` | Record run with metrics |
| GET | `/projects/{id}/experiments/{eid}/runs` | List runs |

---

## Reports

| Method | Path | Description |
|---|---|---|
| POST | `/projects/{id}/reports/generate` | Generate full report |
| GET | `/projects/{id}/reports` | List reports |
| GET | `/projects/{id}/reports/{rid}` | Get report with citations |

---

## Jobs

| Method | Path | Description |
|---|---|---|
| GET | `/projects/{id}/jobs` | List jobs |
| GET | `/projects/{id}/jobs/active` | Get active job |
| GET | `/projects/{id}/jobs/{jid}` | Get job by ID |
| POST | `/projects/{id}/jobs/{jid}/cancel` | Cancel job |

---

## Knowledge Graph

| Method | Path | Description |
|---|---|---|
| GET | `/projects/{id}/knowledge/entities` | List entities |
| GET | `/projects/{id}/knowledge/entities/distribution` | Entity type counts |
| GET | `/projects/{id}/knowledge/relationships` | List relationships |
| GET | `/projects/{id}/knowledge/claims` | List claims with verification status |

---

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | System health check |
