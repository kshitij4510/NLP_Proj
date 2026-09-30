# Development Guide

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — at minimum set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY

# 2. Start infrastructure
docker compose up postgres redis -d

# 3. Run backend (local)
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m spacy download en_core_web_sm
alembic upgrade head
uvicorn app.main:app --reload

# 4. Run worker (separate terminal)
cd backend
python -m app.workers.main

# 5. Run frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Full Docker Stack

```bash
docker compose up --build
```

Access:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Demo Mode

Set `LLM_PROVIDER=demo` in `.env` (the default). The system runs fully without any API keys — LLM calls return placeholder responses, all structure and pipeline logic still executes.

## Adding an LLM Provider

```env
# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Google Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
```

## Development Rules (spec §13)

After **every** implementation phase:
1. Run tests: `pytest backend/tests/`
2. Fix all errors before continuing
3. Verify API endpoints respond correctly
4. Verify database migrations apply cleanly
5. Verify frontend/backend integration
6. Update docs

Do **not** continue with broken functionality.

## Project Structure

```
researchmind/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── agents/       # Workflow state machine
│   │   ├── core/         # Config, security, logging
│   │   ├── database/     # Session, Redis
│   │   ├── evaluation/   # Real metrics computation
│   │   ├── ingestion/    # PDF + academic APIs
│   │   ├── models/       # SQLAlchemy models
│   │   ├── nlp/          # Embeddings, NER, chunking
│   │   ├── repositories/ # Data access layer
│   │   ├── retrieval/    # BM25, dense, hybrid
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── workers/      # ARQ background tasks
│   └── migrations/       # Alembic
├── frontend/
│   └── src/
│       ├── api/          # Axios client + endpoints
│       ├── components/   # UI components
│       ├── features/     # Feature modules
│       ├── hooks/        # React Query hooks
│       ├── layouts/      # Page layouts
│       ├── lib/          # Utilities, store
│       ├── pages/        # Route pages
│       └── types/        # TypeScript types
├── docs/                 # This documentation
├── docker/               # Docker config files
└── docker-compose.yml
```
