# Database Architecture

## Database Schema

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        string full_name
        bool is_active
        timestamp created_at
        timestamp updated_at
    }

    research_projects {
        uuid id PK
        uuid owner_id FK
        string title
        text description
        enum status
        jsonb tags
        timestamp created_at
        timestamp updated_at
    }

    research_questions {
        uuid id PK
        uuid project_id FK
        text question
        jsonb sub_questions
        jsonb keywords
        bool is_primary
    }

    papers {
        uuid id PK
        uuid project_id FK
        string doi
        string arxiv_id
        text title
        text abstract
        int year
        string venue
        int citation_count
        enum status
        float relevance_score
        vector embedding
        timestamp created_at
    }

    paper_chunks {
        uuid id PK
        uuid paper_id FK
        uuid section_id FK
        text content
        int chunk_index
        int page_number
        int token_count
        vector embedding
        jsonb chunk_metadata
    }

    entities {
        uuid id PK
        uuid paper_id FK
        uuid chunk_id FK
        uuid project_id FK
        text name
        text canonical_name
        enum entity_type
        float confidence
        int start_char
        int end_char
        text context_snippet
    }

    relationships {
        uuid id PK
        uuid project_id FK
        uuid source_entity_id FK
        uuid target_entity_id FK
        enum relation_type
        float confidence
        uuid paper_id FK
        uuid chunk_id FK
        text evidence_snippet
    }

    claims {
        uuid id PK
        uuid project_id FK
        uuid paper_id FK
        text claim_text
        enum artifact_type
        enum verification_status
        float confidence
    }

    claim_evidence {
        uuid id PK
        uuid claim_id FK
        uuid paper_id FK
        uuid chunk_id FK
        uuid section_id FK
        int page_number
        text evidence_snippet
        float relevance_score
        enum support_type
    }

    research_gaps {
        uuid id PK
        uuid project_id FK
        string title
        text description
        enum gap_type
        float importance_score
        jsonb supporting_paper_ids
    }

    hypotheses {
        uuid id PK
        uuid project_id FK
        uuid gap_id FK
        text statement
        text rationale
        enum status
        float confidence
        float testability_score
    }

    experiments {
        uuid id PK
        uuid project_id FK
        uuid hypothesis_id FK
        uuid dataset_id FK
        string title
        enum status
        jsonb model_spec
        jsonb hyperparameters
        int random_seed
        jsonb evaluation_metrics
    }

    experiment_runs {
        uuid id PK
        uuid experiment_id FK
        enum status
        string git_commit
        timestamp started_at
        timestamp completed_at
        float runtime_seconds
        jsonb metrics
        jsonb hardware_info
    }

    reports {
        uuid id PK
        uuid project_id FK
        string title
        enum status
        text abstract
        text literature_review
        jsonb verification_summary
        int unsupported_claim_count
    }

    citations {
        uuid id PK
        uuid report_id FK
        uuid paper_id FK
        enum style
        text formatted_citation
        jsonb metadata_snapshot
    }

    research_jobs {
        uuid id PK
        uuid project_id FK
        enum stage
        enum status
        float progress
        int retry_count
        int max_retries
        text error_message
    }

    users ||--o{ research_projects : "owns"
    research_projects ||--o{ research_questions : "has"
    research_projects ||--o{ papers : "contains"
    research_projects ||--o{ research_gaps : "has"
    research_projects ||--o{ hypotheses : "has"
    research_projects ||--o{ experiments : "has"
    research_projects ||--o{ reports : "has"
    research_projects ||--o{ research_jobs : "tracks"
    papers ||--o{ paper_chunks : "split into"
    papers ||--o{ entities : "contains"
    papers ||--o{ claims : "source of"
    entities ||--o{ relationships : "source"
    entities ||--o{ relationships : "target"
    claims ||--o{ claim_evidence : "backed by"
    research_gaps ||--o{ hypotheses : "generates"
    hypotheses ||--o{ experiments : "tested by"
    experiments ||--o{ experiment_runs : "executed as"
    reports ||--o{ citations : "includes"
```

## pgvector Usage

The `paper_chunks.embedding` column stores `vector(384)` (BGE-small dimension).

Key queries:
```sql
-- Cosine similarity search
SELECT id, content, embedding <=> $1 AS distance
FROM paper_chunks
JOIN papers ON paper_chunks.paper_id = papers.id
WHERE papers.project_id = $2
ORDER BY distance
LIMIT 20;

-- HNSW index for production performance
CREATE INDEX ON paper_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Indexes

```sql
-- Full-text search via pg_trgm
CREATE INDEX ON papers USING gin (title gin_trgm_ops);
CREATE INDEX ON paper_chunks USING gin (content gin_trgm_ops);

-- Lookup indexes
CREATE INDEX ON papers (project_id, status);
CREATE INDEX ON paper_chunks (paper_id, chunk_index);
CREATE INDEX ON entities (project_id, entity_type);
CREATE INDEX ON claims (project_id, verification_status);
CREATE INDEX ON research_jobs (project_id, status);
```
