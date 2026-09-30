# ResearchMind — System Architecture

## Overview

ResearchMind is an evidence-grounded autonomous NLP research system. It is **not** a chatbot and **not** a simple RAG application. Every claim in the system maps to a specific paper, page, section, and chunk. Every citation is generated from stored metadata — never from an LLM.

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

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[React + TypeScript]
        ROUTER[React Router]
        STATE[Zustand Store]
        QUERY[React Query]
    end

    subgraph "API Layer"
        FASTAPI[FastAPI]
        AUTH[JWT Auth]
        RATELIMIT[Rate Limiter]
        CORS[CORS Middleware]
    end

    subgraph "Service Layer"
        PS[ProjectService]
        PPS[PaperService]
        RS[RetrievalService]
        SS[SynthesisService]
        GS[GapService]
        HS[HypothesisService]
        ES[ExperimentService]
        VS[VerificationService]
        CS[CitationService]
        RPS[ReportService]
        JS[JobService]
    end

    subgraph "Agent Layer"
        WR[WorkflowRunner]
        SH[Stage Handlers x11]
        SM[State Machine]
    end

    subgraph "NLP Layer"
        EMB[EmbeddingEngine BGE]
        NER[ScientificNER]
        KP[KeyphraseExtractor]
        RE[RelationExtractor]
        CH[Chunker]
        EP[ExtractionPipeline]
    end

    subgraph "Retrieval Layer"
        BM25[BM25Retriever]
        DENSE[DenseRetriever]
        RERANK[CrossEncoderReranker]
        HYBRID[HybridRetriever RRF]
    end

    subgraph "Ingestion Layer"
        PDF[PDFProcessor]
        DL[Downloader]
        SS_API[Semantic Scholar]
        OA[OpenAlex]
        AR[arXiv]
        IP[IngestionPipeline]
    end

    subgraph "Infrastructure"
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis)]
        WORKER[ARQ Worker]
    end

    UI --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> PS & PPS & RS
    PS & PPS & RS --> Service Layer
    Service Layer --> WR
    WR --> SH
    SH --> NLP Layer
    SH --> Retrieval Layer
    SH --> Ingestion Layer
    NLP Layer --> PG
    Retrieval Layer --> PG
    Ingestion Layer --> DL
    DL --> SS_API & OA & AR
    Service Layer --> PG
    Service Layer --> REDIS
    WORKER --> REDIS
    WORKER --> Service Layer
```

## Architecture Priorities

| Priority | Over |
|---|---|
| FUNCTIONALITY | UI animation |
| EVIDENCE | LLM-generated claims |
| REPRODUCIBILITY | Autonomous behavior |
| MEASURED RESULTS | Fabricated metrics |
| MODULARITY | Monolithic implementation |
| TRACEABILITY | Opaque reasoning |

## Layer Responsibilities

### Presentation Layer
- React + TypeScript + Tailwind CSS
- User interaction, visualization, workflow status
- **No core research logic**

### API Layer (FastAPI)
- Authentication, authorization, rate limiting
- Input validation, request routing
- Returns structured JSON — never raw LLM text

### Service Layer
- All business logic
- 11 services: project, paper, retrieval, synthesis, gap, hypothesis, experiment, verification, citation, report, job

### Agent/Workflow Layer
- State machine: 11 stages, linear transitions
- No uncontrolled recursive agents
- Every stage: typed input → typed output → persisted status

### NLP Layer
- Local models (spaCy, sentence-transformers, KeyBERT)
- All extractions retain provenance (paper_id, chunk_id, char offsets)

### Retrieval Layer
- BM25 sparse + pgvector dense → RRF fusion → cross-encoder rerank
- Every result exposes all score components

### Infrastructure
- PostgreSQL + pgvector: relational data + vector retrieval + knowledge graph
- Redis: job queue, caching, job state
- No Neo4j unless profiling proves necessity (spec §14)
