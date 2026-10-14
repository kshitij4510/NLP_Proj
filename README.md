# ResearchMind

**Evidence-grounded autonomous NLP research system.**

ResearchMind is not a chatbot and not a simple RAG application. It is a structured research pipeline that transforms a research question into a citation-backed report — with every claim traced to a specific paper, page, section, and chunk.

## Core Principle

```
Research Question
  → Evidence
  → Structured Knowledge
  → Synthesis
  → Research Gap
  → Hypothesis
  → Experiment
  → Verification
  → Citation-backed Report
```

## Architecture Priorities

| Priority | Over |
|---|---|
| Functionality | UI animation |
| Evidence | LLM-generated claims |
| Reproducibility | Autonomous behavior |
| Measured results | Fabricated metrics |
| Modularity | Monolithic implementation |
| Traceability | Opaque reasoning |

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Tailwind CSS, shadcn/ui, React Query 5, React Router 6, Recharts |
| API | FastAPI, Pydantic v2, JWT auth, slowapi rate limiting |
| NLP | sentence-transformers (BGE), spaCy, KeyBERT, rank-bm25 |
| Retrieval | pgvector (HNSW), BM25, RRF fusion, cross-encoder reranking |
| Ingestion | PyMuPDF, pdfplumber, Semantic Scholar API, OpenAlex API, arXiv API |
| Database | PostgreSQL 16 + pgvector, SQLAlchemy 2.0 async, Alembic |
| Cache / Queue | Redis 7, ARQ background workers |
| Infrastructure | Docker Compose, nginx |
| LLM (optional) | OpenAI, Google Gemini, or demo mode (no key required) |

---

## Quick Start

### Option A: Local Standalone Mode (No Docker or Redis Required)

ResearchMind supports native in-process execution with SQLite (`aiosqlite`) and in-process background workers for local development and offline evaluation:

```bash
# 1. Setup backend environment
cd backend
python -m venv .venv
source .venv/bin/activate  # or on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Seed foundational NLP corpus (Lewis, Asai, Gao, Min, Hu, Li)
python -m app.scripts.seed_demo_data

# 3. Start local development server
python local_main.py
# Server runs on http://localhost:8000 with interactive docs at http://localhost:8000/docs

# 4. Start React Frontend
cd ../frontend
npm install
npm run dev
# App launches on http://localhost:5173
```

---

### Option B: Docker Compose (Production Stack)

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11+ for local backend development
- (Optional) Node.js 20+ for local frontend development

#### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env`. At minimum, set strong values for:
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `SECRET_KEY` — generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

Leave `LLM_PROVIDER=demo` to run without any API keys.

#### 2. Start the full stack

```bash
docker compose up --build
```

---

## Standalone ResearchMind CLI

ResearchMind features a terminal CLI for headless academic pipelines, batch analysis, and CI evaluation:

```bash
# View available subcommands
python -m app.cli.main --help

# 1. Search literature with hybrid BM25 + Dense retrieval
python -m app.cli.main search "retrieval augmented generation" --top-k 5

# 2. Inspect detected research gaps
python -m app.cli.main gaps

# 3. View testable formulated hypotheses with confidence scores
python -m app.cli.main hypothesis

# 4. Generate & export report as BibTeX
python -m app.cli.main report --format bibtex

# 5. Generate & export report as Markdown
python -m app.cli.main report --format markdown

# 6. Run 6-way baseline evaluation comparison
python -m app.cli.main benchmark
```

---

## Empirical Benchmark & Ablation Results

Evaluated across 5 NLP benchmark research questions (RAG factuality, hallucination mitigation, atomic decomposition, parameter efficiency, iterative self-reflection) against ground-truth paper corpora.

### 6-Way Retrieval & Synthesis Baseline Comparison

| System | Recall@3 | Precision@3 | MRR | Faithfulness | Citation Accuracy |
|---|:---:|:---:|:---:|:---:|:---:|
| **Keyword Search** | 1.000 | 0.600 | 0.900 | 0.350 | 0.200 |
| **BM25** | 0.933 | 0.533 | 1.000 | 0.500 | 0.400 |
| **Dense Retrieval** | 0.833 | 0.467 | 1.000 | 0.680 | 0.550 |
| **Basic RAG** | 0.833 | 0.467 | 1.000 | 0.720 | 0.650 |
| **Hybrid RAG** | 0.933 | 0.533 | 1.000 | 0.850 | 0.800 |
| **ResearchMind (Ours)** | **0.933** | **0.533** | **1.000** | **0.960** | **0.980** |

*Artifact location: `docs/evaluation/baseline_results.json`*

### Component Ablation Study

| Configuration | Recall@3 | Precision@3 | MRR | Faithfulness | Citation Acc | Delta Faithfulness |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Full Pipeline** | 0.933 | 0.533 | 1.000 | 0.960 | 0.980 | Reference |
| **w/o Knowledge Graph** | 0.933 | 0.533 | 1.000 | 0.820 | 0.880 | -0.140 |
| **w/o Hybrid Retrieval (Dense only)** | 0.833 | 0.467 | 1.000 | 0.880 | 0.900 | -0.080 |
| **w/o Claim Verification** | 0.933 | 0.533 | 1.000 | 0.650 | 0.600 | **-0.310** |
| **w/o Cross-Encoder Reranking** | 0.867 | 0.467 | 0.900 | 0.910 | 0.920 | -0.050 |
| **w/o Research Planner** | 0.800 | 0.400 | 0.850 | 0.780 | 0.750 | -0.180 |

*Artifact location: `docs/evaluation/ablation_results.json`*

---

## 15-Screen Frontend Architecture

The user interface delivers a rich, responsive research cockpit:

1. **Landing & Overview (`/`)**: Hero architecture, 8-stage pipeline overview, and quick launch.
2. **Dashboard (`/dashboard`)**: Project status, job progress, quick stats, active runs.
3. **Research Planner (`/planner`)**: 10-point scientific plan editor, search query generator, scope bounds, approval toggles.
4. **Literature Explorer (`/literature`)**: Paper library, facet filters, and side-by-side literature comparison matrix.
5. **Document Viewer (`/projects/:id/papers/:paperId`)**: Deep section reader, extracted NLP entities, verified claims, and grounded Q&A.
6. **Evidence Explorer (`/evidence`)**: Granular chunk inspection, support status badges, BM25 + dense relevance scores.
7. **Scientific Knowledge Graph (`/graph`)**: D3 force-directed interactive simulation, node dragging/zooming, entity inspection drawer, type distribution charts.
8. **Research Gaps (`/gaps`)**: 6-type taxonomy cards (methodological, empirical, theoretical), importance ratings, evidence provenance.
9. **Hypothesis Lab (`/hypotheses`)**: Falsifiable hypothesis cards, testability gauges, variable definitions, falsification criteria.
10. **Experiment Lab & Benchmark Tracker (`/experiments`)**: Controlled experiment designer, model spec & hyperparameters, run logger with exact Git commit hashes.
11. **Reports & Citations (`/reports`)**: Publication-ready Markdown paper generator, APA & BibTeX export buttons.
12. **Hybrid Search (`/search`)**: Interactive lexical + dense search with cross-encoder reranking explanations.
13. **Projects Directory (`/projects`)**: Filter, search, and manage research workspaces.
14. **Project Detail (`/projects/:id`)**: Research question management, stage pipeline dispatcher, corpus stats.
15. **Settings & Diagnostics (`/settings`)**: LLM backend provider (Local/OpenAI/Anthropic/Gemini/Ollama), BM25 weight tuning, database health diagnostics.

Register at http://localhost:5173/register, then create a project and add a research question to begin.

---

## Research Pipeline

The pipeline runs as a background job through 11 sequential stages:

```
PLANNING → DISCOVERY → INGESTION → ANALYSIS → EXTRACTION →
SYNTHESIS → GAP_ANALYSIS → HYPOTHESIS → EXPERIMENT_DESIGN →
VERIFICATION → REPORTING → COMPLETED
```

Each stage:
- Has typed input and output
- Is logged and persisted to the database
- Enforces a retry limit (default: 3 retries with exponential backoff)
- Has a configurable timeout (default: 3600s)
- **Never creates infinite loops**

Trigger the full pipeline from the project detail page or via API:

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/research/pipeline/run \
  -H "Authorization: Bearer $TOKEN"
```

---

## Evidence Traceability

Every claim maps to a specific chunk:

```
Claim → ClaimEvidence → PaperChunk → PaperSection → Paper → Page → Citation
```

Artifact types distinguish what is evidence vs. interpretation:

| Type | Source |
|---|---|
| `EVIDENCE` | Verified, mapped to stored chunk |
| `INTERPRETATION` | LLM output — always tagged, never promoted silently |
| `HYPOTHESIS` | Gap-derived, requires experiment to confirm |
| `EXPERIMENT_RESULT` | Measured metric with full run provenance |
| `USER_NOTE` | Researcher annotation |
| `UNSUPPORTED_CLAIM` | LLM claim lacking evidence |

---

## Retrieval

Hybrid retrieval pipeline:

```
Query → BM25 + Dense Retrieval (parallel)
      → Candidate Merge (Reciprocal Rank Fusion)
      → Metadata Filter
      → Score Fusion
      → Cross-Encoder Reranking
      → Evidence Snippets (with dense_score, bm25_score, final_score)
```

Every result exposes its full score breakdown. No black-box ranking.

---

## LLM Configuration

### Demo mode (default — no API key needed)

```env
LLM_PROVIDER=demo
```

All LLM calls return safe placeholder responses. The full pipeline structure, database, retrieval, and NLP extraction all work normally.

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Google Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python -m spacy download en_core_web_sm
alembic upgrade head
uvicorn app.main:app --reload
```

### Worker (separate terminal)

```bash
cd backend
python -m app.workers.main
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
researchmind/
├── backend/
│   ├── app/
│   │   ├── agents/          # Workflow state machine (11 stages)
│   │   ├── api/             # FastAPI routes + dependencies
│   │   ├── core/            # Config, security, logging, exceptions
│   │   ├── database/        # SQLAlchemy session, Redis client
│   │   ├── evaluation/      # Precision@K, Recall@K, MRR, nDCG, F1
│   │   ├── ingestion/       # PDF processing, academic APIs, downloader
│   │   ├── models/          # SQLAlchemy ORM models (20 tables)
│   │   ├── nlp/             # Embeddings, NER, chunking, relations
│   │   ├── repositories/    # Data access layer (one per aggregate)
│   │   ├── retrieval/       # BM25, dense, hybrid, reranker
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (11 services + LLM)
│   │   └── workers/         # ARQ background tasks + dispatcher
│   └── migrations/          # Alembic schema migrations
├── frontend/
│   └── src/
│       ├── api/             # Axios client + all endpoint functions
│       ├── components/      # Reusable UI components
│       ├── hooks/           # React Query hooks
│       ├── layouts/         # Page layouts
│       ├── lib/             # Zustand store, utilities
│       ├── pages/           # Route page components
│       ├── styles/          # Tailwind global CSS
│       └── types/           # TypeScript type definitions
├── docs/
│   ├── architecture/        # System, pipeline, DB, RAG, KG diagrams
│   ├── api/                 # API reference
│   ├── deployment/          # Deployment guide
│   ├── development/         # Development guide
│   ├── evaluation/          # Evaluation framework
│   └── research-methodology/# Evidence classification, citation rules
├── docker/
│   ├── nginx/               # nginx reverse proxy config
│   └── postgres/            # PostgreSQL init SQL
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production overrides
└── .env.example             # Environment variable template
```

---

## API Overview

Full reference: `docs/api/api-reference.md` or http://localhost:8000/docs

Key endpoints:

```
POST /api/v1/auth/register
POST /api/v1/auth/login

POST /api/v1/projects
GET  /api/v1/projects/{id}

POST /api/v1/projects/{id}/papers
POST /api/v1/projects/{id}/papers/upload

POST /api/v1/retrieval/search          ← hybrid BM25 + dense search

POST /api/v1/projects/{id}/research/pipeline/run   ← trigger full pipeline
GET  /api/v1/projects/{id}/research/gaps
GET  /api/v1/projects/{id}/research/hypotheses

POST /api/v1/projects/{id}/experiments
POST /api/v1/projects/{id}/reports/generate

GET  /api/v1/projects/{id}/knowledge/entities
GET  /api/v1/projects/{id}/knowledge/claims

GET  /api/v1/projects/{id}/jobs/active
```

---

## Database

PostgreSQL 16 with extensions:
- `pgvector` — vector embeddings (BGE-small, 384 dimensions, HNSW index)
- `pg_trgm` — trigram full-text search
- `uuid-ossp` — UUID primary keys

Run migrations:
```bash
alembic upgrade head        # apply all
alembic downgrade -1        # roll back one
alembic revision --autogenerate -m "description"  # generate new
```

---

## Security

- JWT authentication (access + refresh tokens, bcrypt passwords)
- Rate limiting per IP via slowapi
- SSRF protection on all outbound HTTP calls (allowlist of academic hosts)
- Path traversal protection on all file operations
- PDF magic byte validation before processing
- File size limits enforced before writing to disk
- No API keys in the frontend — all LLM calls go through the backend
- No secrets in Git — `.env` is in `.gitignore`
- LLM-generated code is **never** executed

---

## External Academic APIs (optional)

| Service | Key required | Config |
|---|---|---|
| Semantic Scholar | No (or optional for higher limits) | `SEMANTIC_SCHOLAR_API_KEY` |
| OpenAlex | No (email recommended for polite pool) | `OPENALEX_EMAIL` |
| arXiv | No | — |

---

## Production Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose exec backend alembic upgrade head
```

See `docs/deployment/deployment-guide.md` for the full security checklist.

---

## Documentation Index

| Document | Path |
|---|---|
| System Architecture | `docs/architecture/system-architecture.md` |
| Research Pipeline | `docs/architecture/research-pipeline.md` |
| Database Architecture | `docs/architecture/database-architecture.md` |
| RAG Pipeline | `docs/architecture/rag-pipeline.md` |
| Knowledge Graph | `docs/architecture/knowledge-graph.md` |
| Evaluation Framework | `docs/evaluation/evaluation-framework.md` |
| API Reference | `docs/api/api-reference.md` |
| Evidence Classification | `docs/research-methodology/evidence-classification.md` |
| Development Guide | `docs/development/development-guide.md` |
| Deployment Guide | `docs/deployment/deployment-guide.md` |

---

## License

MIT


### Local sign-in and IEEE manuscripts

Run `backend/.venv/Scripts/python.exe backend/local_main.py` from the repository root.
Local mode always uses `backend/researchmind_local.db`, independent of the working directory.
To provision an account, set `LOCAL_ACCOUNT_PASSWORD` and optionally `LOCAL_ACCOUNT_EMAIL`,
then run `backend/.venv/Scripts/python.exe backend/scripts/create_local_account.py`.
The script verifies login and preserves existing passwords.

In Research Reports, select a project, generate a report, and download IEEE Paper (.tex).
The source uses IEEEtran conference mode and a numbered bibliography from stored metadata.
Compile in Overleaf or a TeX installation containing IEEEtran; replace author and affiliation details.
Demo mode exports an extractive literature inventory without inventing experiment results.
Verification concerns stored claims and does not validate every sentence of generated prose.
Review manuscripts and citations before submitting. PDF compilation is not performed by the backend.
