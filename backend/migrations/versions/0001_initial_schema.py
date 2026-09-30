"""Initial schema — all ResearchMind tables

Revision ID: 0001
Revises: 
Create Date: 2026-09-02 00:00:00.000000

"""
from __future__ import annotations
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── Enums ─────────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE project_status AS ENUM ('created','planning','active','paused','completed','archived')")
    op.execute("CREATE TYPE paper_status AS ENUM ('discovered','downloading','downloaded','processing','processed','failed','skipped')")
    op.execute("CREATE TYPE entity_type AS ENUM ('MODEL','DATASET','TASK','METRIC','METHOD','BENCHMARK','ORGANIZATION','AUTHOR','CONCEPT')")
    op.execute("CREATE TYPE relation_type AS ENUM ('evaluated_on','achieves','improves','compared_with','cites','used_for','supports','contradicts','based_on','authored_by','uses','compares_with')")
    op.execute("CREATE TYPE verification_status AS ENUM ('SUPPORTED','PARTIALLY_SUPPORTED','CONTRADICTED','INSUFFICIENT_EVIDENCE','PENDING')")
    op.execute("CREATE TYPE artifact_type AS ENUM ('EVIDENCE','INTERPRETATION','HYPOTHESIS','EXPERIMENT_RESULT','USER_NOTE','UNSUPPORTED_CLAIM')")
    op.execute("CREATE TYPE gap_type AS ENUM ('methodological','empirical','theoretical','application','replication','data')")
    op.execute("CREATE TYPE hypothesis_status AS ENUM ('draft','active','testing','supported','refuted','inconclusive')")
    op.execute("CREATE TYPE experiment_status AS ENUM ('draft','queued','running','completed','failed','cancelled')")
    op.execute("CREATE TYPE report_status AS ENUM ('draft','generating','verifying','completed','failed')")
    op.execute("CREATE TYPE citation_style AS ENUM ('apa','ieee','bibtex')")
    op.execute("CREATE TYPE job_stage AS ENUM ('PLANNING','DISCOVERY','INGESTION','ANALYSIS','EXTRACTION','SYNTHESIS','GAP_ANALYSIS','HYPOTHESIS','EXPERIMENT_DESIGN','VERIFICATION','REPORTING','COMPLETED')")
    op.execute("CREATE TYPE job_status AS ENUM ('pending','running','completed','failed','cancelled','retrying')")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── research_projects ─────────────────────────────────────────────────────
    op.create_table(
        "research_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.Text, nullable=False, server_default="created"),
        sa.Column("tags", postgresql.JSONB, server_default="[]"),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_research_projects_owner_id", "research_projects", ["owner_id"])

    # ── research_questions ────────────────────────────────────────────────────
    op.create_table(
        "research_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("sub_questions", postgresql.JSONB, server_default="[]"),
        sa.Column("scope", sa.Text),
        sa.Column("keywords", postgresql.JSONB, server_default="[]"),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_research_questions_project_id", "research_questions", ["project_id"])

    # ── papers ────────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doi", sa.String(255)),
        sa.Column("arxiv_id", sa.String(100)),
        sa.Column("semantic_scholar_id", sa.String(100)),
        sa.Column("openalex_id", sa.String(100)),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("abstract", sa.Text),
        sa.Column("year", sa.Integer),
        sa.Column("venue", sa.String(500)),
        sa.Column("citation_count", sa.Integer, server_default="0"),
        sa.Column("reference_count", sa.Integer, server_default="0"),
        sa.Column("pdf_url", sa.Text),
        sa.Column("local_pdf_path", sa.Text),
        sa.Column("source", sa.String(50), server_default="unknown"),
        sa.Column("status", sa.Text, nullable=False, server_default="discovered"),
        sa.Column("raw_metadata", postgresql.JSONB),
        sa.Column("relevance_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("project_id", "doi", name="uq_paper_project_doi"),
    )
    op.create_index("ix_papers_project_id", "papers", ["project_id"])
    op.create_index("ix_papers_doi", "papers", ["doi"])
    op.create_index("ix_papers_arxiv_id", "papers", ["arxiv_id"])
    op.execute("CREATE INDEX ix_papers_title_trgm ON papers USING gin (title gin_trgm_ops)")

    # ── paper_authors ─────────────────────────────────────────────────────────
    op.create_table(
        "paper_authors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("affiliation", sa.Text),
        sa.Column("orcid", sa.String(50)),
        sa.Column("position", sa.Integer, server_default="0"),
    )
    op.create_index("ix_paper_authors_paper_id", "paper_authors", ["paper_id"])

    # ── paper_sections ────────────────────────────────────────────────────────
    op.create_table(
        "paper_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("section_type", sa.String(100)),
        sa.Column("page_start", sa.Integer),
        sa.Column("page_end", sa.Integer),
        sa.Column("position", sa.Integer, server_default="0"),
    )
    op.create_index("ix_paper_sections_paper_id", "paper_sections", ["paper_id"])

    # ── paper_chunks (with pgvector) ──────────────────────────────────────────
    op.create_table(
        "paper_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_sections.id", ondelete="SET NULL")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, server_default="0"),
        sa.Column("page_number", sa.Integer),
        sa.Column("token_count", sa.Integer),
        sa.Column("embedding", sa.Text),  # Actual vector type applied below
        sa.Column("chunk_metadata", postgresql.JSONB),
    )
    op.create_index("ix_paper_chunks_paper_id", "paper_chunks", ["paper_id"])
    op.create_index("ix_paper_chunks_section_id", "paper_chunks", ["section_id"])
    # Change column type to vector(384) after table creation
    op.execute("ALTER TABLE paper_chunks ALTER COLUMN embedding TYPE vector(384) USING NULL::vector(384)")
    op.execute("CREATE INDEX ix_paper_chunks_embedding_hnsw ON paper_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")
    op.execute("CREATE INDEX ix_paper_chunks_content_trgm ON paper_chunks USING gin (content gin_trgm_ops)")

    # ── entities ──────────────────────────────────────────────────────────────
    op.create_table(
        "entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_chunks.id", ondelete="SET NULL")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("canonical_name", sa.Text),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("start_char", sa.Integer),
        sa.Column("end_char", sa.Integer),
        sa.Column("context_snippet", sa.Text),
        sa.Column("attributes", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_entities_project_id", "entities", ["project_id"])
    op.create_index("ix_entities_paper_id", "entities", ["paper_id"])
    op.create_index("ix_entities_entity_type", "entities", ["entity_type"])

    # ── relationships ─────────────────────────────────────────────────────────
    op.create_table(
        "relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL")),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_chunks.id", ondelete="SET NULL")),
        sa.Column("evidence_snippet", sa.Text),
        sa.Column("attributes", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_relationships_project_id", "relationships", ["project_id"])
    op.create_index("ix_relationships_source_entity_id", "relationships", ["source_entity_id"])
    op.create_index("ix_relationships_target_entity_id", "relationships", ["target_entity_id"])

    # ── claims ────────────────────────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL")),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column("artifact_type", sa.Text, nullable=False, server_default="UNSUPPORTED_CLAIM"),
        sa.Column("verification_status", sa.Text, nullable=False, server_default="PENDING"),
        sa.Column("confidence", sa.Float),
        sa.Column("source_chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_chunks.id", ondelete="SET NULL")),
        sa.Column("attributes", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_claims_project_id", "claims", ["project_id"])
    op.create_index("ix_claims_verification_status", "claims", ["verification_status"])

    # ── claim_evidence ────────────────────────────────────────────────────────
    op.create_table(
        "claim_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_chunks.id", ondelete="SET NULL")),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("paper_sections.id", ondelete="SET NULL")),
        sa.Column("page_number", sa.Integer),
        sa.Column("evidence_snippet", sa.Text, nullable=False),
        sa.Column("relevance_score", sa.Float, server_default="1.0"),
        sa.Column("support_type", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_claim_evidence_claim_id", "claim_evidence", ["claim_id"])
    op.create_index("ix_claim_evidence_paper_id", "claim_evidence", ["paper_id"])

    # ── research_gaps ─────────────────────────────────────────────────────────
    op.create_table(
        "research_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("gap_type", sa.Text, nullable=False),
        sa.Column("importance_score", sa.Float),
        sa.Column("supporting_paper_ids", postgresql.JSONB, server_default="[]"),
        sa.Column("evidence_snippets", postgresql.JSONB, server_default="[]"),
        sa.Column("detected_by", sa.String(100), server_default="synthesis"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_research_gaps_project_id", "research_gaps", ["project_id"])

    # ── hypotheses ────────────────────────────────────────────────────────────
    op.create_table(
        "hypotheses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gap_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_gaps.id", ondelete="SET NULL")),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text),
        sa.Column("status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("confidence", sa.Float),
        sa.Column("supporting_evidence", postgresql.JSONB, server_default="[]"),
        sa.Column("testability_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_hypotheses_project_id", "hypotheses", ["project_id"])

    # ── datasets ──────────────────────────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("source_url", sa.Text),
        sa.Column("version", sa.String(100)),
        sa.Column("size_info", postgresql.JSONB),
        sa.Column("splits", postgresql.JSONB),
        sa.Column("license", sa.String(200)),
        sa.Column("attributes", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── experiments ───────────────────────────────────────────────────────────
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hypothesis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hypotheses.id", ondelete="SET NULL")),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasets.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("model_spec", postgresql.JSONB),
        sa.Column("baseline_spec", postgresql.JSONB),
        sa.Column("hyperparameters", postgresql.JSONB),
        sa.Column("random_seed", sa.Integer),
        sa.Column("preprocessing_steps", postgresql.JSONB),
        sa.Column("evaluation_metrics", postgresql.JSONB),
        sa.Column("ablations", postgresql.JSONB),
        sa.Column("statistical_tests", postgresql.JSONB),
        sa.Column("hardware_requirements", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_experiments_project_id", "experiments", ["project_id"])

    # ── experiment_runs ───────────────────────────────────────────────────────
    op.create_table(
        "experiment_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="queued"),
        sa.Column("git_commit", sa.String(40)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("runtime_seconds", sa.Float),
        sa.Column("hardware_info", postgresql.JSONB),
        sa.Column("model_config_snapshot", postgresql.JSONB),
        sa.Column("hyperparameter_snapshot", postgresql.JSONB),
        sa.Column("metrics", postgresql.JSONB),
        sa.Column("artifacts", postgresql.JSONB),
        sa.Column("logs", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_experiment_runs_experiment_id", "experiment_runs", ["experiment_id"])

    # ── metrics ───────────────────────────────────────────────────────────────
    op.create_table(
        "metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("split", sa.String(50)),
        sa.Column("step", sa.Integer),
        sa.Column("attributes", postgresql.JSONB),
    )
    op.create_index("ix_metrics_run_id", "metrics", ["run_id"])

    # ── reports ───────────────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("abstract", sa.Text),
        sa.Column("research_question_section", sa.Text),
        sa.Column("background", sa.Text),
        sa.Column("literature_review", sa.Text),
        sa.Column("research_landscape", sa.Text),
        sa.Column("method_comparison", sa.Text),
        sa.Column("research_gaps_section", sa.Text),
        sa.Column("hypotheses_section", sa.Text),
        sa.Column("experimental_design", sa.Text),
        sa.Column("results", sa.Text),
        sa.Column("ablation_study", sa.Text),
        sa.Column("limitations", sa.Text),
        sa.Column("future_work", sa.Text),
        sa.Column("conclusion", sa.Text),
        sa.Column("verification_summary", postgresql.JSONB),
        sa.Column("unsupported_claim_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_reports_project_id", "reports", ["project_id"])

    # ── citations ─────────────────────────────────────────────────────────────
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("style", sa.Text, nullable=False),
        sa.Column("formatted_citation", sa.Text, nullable=False),
        sa.Column("in_text_citation", sa.String(200)),
        sa.Column("metadata_snapshot", postgresql.JSONB),
    )
    op.create_index("ix_citations_report_id", "citations", ["report_id"])
    op.create_index("ix_citations_paper_id", "citations", ["paper_id"])

    # ── research_notes ────────────────────────────────────────────────────────
    op.create_table(
        "research_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="SET NULL")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("note_type", sa.String(50), server_default="general"),
        sa.Column("tags", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── research_jobs ─────────────────────────────────────────────────────────
    op.create_table(
        "research_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("progress", sa.Float, server_default="0.0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("max_retries", sa.Integer, server_default="3"),
        sa.Column("error_message", sa.Text),
        sa.Column("job_metadata", postgresql.JSONB),
        sa.Column("worker_job_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_research_jobs_project_id", "research_jobs", ["project_id"])
    op.create_index("ix_research_jobs_stage", "research_jobs", ["stage"])
    op.create_index("ix_research_jobs_status", "research_jobs", ["status"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    for table in [
        "research_jobs", "research_notes", "citations", "reports",
        "metrics", "experiment_runs", "experiments", "datasets",
        "hypotheses", "research_gaps", "claim_evidence", "claims",
        "relationships", "entities", "paper_chunks", "paper_sections",
        "paper_authors", "papers", "research_questions",
        "research_projects", "users",
    ]:
        op.drop_table(table)

    for enum in [
        "job_status", "job_stage", "citation_style", "report_status",
        "experiment_status", "hypothesis_status", "gap_type",
        "artifact_type", "verification_status", "relation_type",
        "entity_type", "paper_status", "project_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
