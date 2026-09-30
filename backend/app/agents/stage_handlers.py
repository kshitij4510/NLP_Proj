"""
Stage handler implementations.
Each handler is a pure async function: (context, db) → StageOutput.
Typed input/output, retry policy enforced by the workflow runner.
No handler spawns new agents or recursive calls.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.states import (
    AnalysisInput, AnalysisOutput,
    DiscoveryInput, DiscoveryOutput,
    ExperimentDesignInput, ExperimentDesignOutput,
    ExtractionInput, ExtractionOutput,
    GapAnalysisInput, GapAnalysisOutput,
    HypothesisInput, HypothesisOutput,
    IngestionInput, IngestionOutput,
    PlanningInput, PlanningOutput,
    ReportingInput, ReportingOutput,
    SynthesisInput, SynthesisOutput,
    VerificationInput, VerificationOutput,
    WorkflowContext,
)
from app.core.logging import get_logger
from app.models.job import JobStage

logger = get_logger(__name__)


async def handle_planning(ctx: WorkflowContext, db: AsyncSession) -> PlanningOutput:
    """
    Expand the research question into a set of search queries.
    Uses LLM to generate query variations; falls back to keywords.
    """
    from app.services.llm_service import LLMService
    from app.repositories.project_repo import ResearchQuestionRepository

    q_repo = ResearchQuestionRepository(db)
    project_id = uuid.UUID(ctx.project_id)
    question = await q_repo.get_primary(project_id)
    question_text = question.question if question else ctx.stage_outputs.get("query", "")

    llm = LLMService()
    prompt = f"""Generate 3-5 academic search queries for this research question.
Question: {question_text}
Output JSON: {{"queries": ["query1", "query2", ...], "sources": ["semantic_scholar", "openalex", "arxiv"]}}"""

    raw = await llm.generate_json(prompt)
    queries = raw.get("queries", [question_text])
    sources = raw.get("sources", ["semantic_scholar", "openalex", "arxiv"])

    if not queries:
        queries = [question_text]

    output = PlanningOutput(
        search_queries=queries[:5],
        sources=sources,
        plan_summary=f"Generated {len(queries)} search queries for: {question_text[:100]}",
    )
    logger.info("stage.planning.complete", project_id=ctx.project_id, queries=len(queries))
    return output


async def handle_discovery(ctx: WorkflowContext, db: AsyncSession) -> DiscoveryOutput:
    """Discover papers from academic APIs using planned queries."""
    from app.ingestion.ingestion_pipeline import IngestionPipeline

    planning_out: PlanningOutput = ctx.stage_outputs.get(JobStage.PLANNING.value)
    queries = planning_out.search_queries if planning_out else ["machine learning"]
    sources = planning_out.sources if planning_out else ["semantic_scholar", "arxiv"]

    pipeline = IngestionPipeline(db)
    project_id = uuid.UUID(ctx.project_id)

    total_added, total_skipped = 0, 0
    for query in queries:
        result = await pipeline.run_discovery(
            project_id=project_id,
            query=query,
            limit_per_source=15,
            sources=sources,
        )
        total_added += result.get("added", 0)
        total_skipped += result.get("skipped", 0)

    output = DiscoveryOutput(
        discovered=total_added + total_skipped,
        added=total_added,
        skipped=total_skipped,
    )
    logger.info("stage.discovery.complete", project_id=ctx.project_id, added=total_added)
    return output


async def handle_ingestion(ctx: WorkflowContext, db: AsyncSession) -> IngestionOutput:
    """Download PDFs and run initial extraction for discovered papers."""
    from app.ingestion.ingestion_pipeline import IngestionPipeline

    pipeline = IngestionPipeline(db)
    project_id = uuid.UUID(ctx.project_id)
    result = await pipeline.run_ingestion(project_id=project_id, batch_size=10)

    output = IngestionOutput(
        processed=result.get("processed", 0),
        failed=result.get("failed", 0),
    )
    logger.info("stage.ingestion.complete", project_id=ctx.project_id, **result)
    return output


async def handle_analysis(ctx: WorkflowContext, db: AsyncSession) -> AnalysisOutput:
    """
    Compute embeddings for any chunks that don't have them yet.
    This handles papers that were added without going through full ingestion.
    """
    from app.nlp.embeddings import get_embedding_engine
    from app.repositories.paper_repo import PaperChunkRepository

    project_id = uuid.UUID(ctx.project_id)
    chunk_repo = PaperChunkRepository(db)

    # Find chunks without embeddings
    chunks = await chunk_repo.list_by_project_without_embeddings(project_id, limit=1000)
    if not chunks:
        output = AnalysisOutput(chunks_with_embeddings=0)
        logger.info("stage.analysis.no_work", project_id=ctx.project_id)
        return output

    engine = get_embedding_engine()
    texts = [c.content for c in chunks]
    embeddings = await engine.encode(texts, batch_size=32)

    updates = [(c.id, emb) for c, emb in zip(chunks, embeddings)]
    count = await chunk_repo.bulk_update_embeddings(updates)

    output = AnalysisOutput(chunks_with_embeddings=count)
    logger.info("stage.analysis.complete", project_id=ctx.project_id, embedded=count)
    return output


async def handle_extraction(ctx: WorkflowContext, db: AsyncSession) -> ExtractionOutput:
    """Aggregate NER and relation extraction stats across the project."""
    from app.repositories.knowledge_repo import EntityRepository, RelationshipRepository

    project_id = uuid.UUID(ctx.project_id)
    entity_repo = EntityRepository(db)
    rel_repo = RelationshipRepository(db)

    _, entity_count = await entity_repo.list_by_project(project_id, limit=1)
    _, rel_count = await rel_repo.list_by_project(project_id, limit=1)

    output = ExtractionOutput(
        entities_extracted=entity_count,
        relations_extracted=rel_count,
    )
    logger.info(
        "stage.extraction.complete",
        project_id=ctx.project_id,
        entities=entity_count,
        relations=rel_count,
    )
    return output


async def handle_synthesis(ctx: WorkflowContext, db: AsyncSession) -> SynthesisOutput:
    """Generate literature synthesis grounded in retrieved evidence."""
    from app.services.research_service import ResearchService

    project_id = uuid.UUID(ctx.project_id)
    research_svc = ResearchService(db)

    # Run synthesis sub-pipeline (retrieval → synthesis only)
    from app.services.retrieval_service import RetrievalService
    from app.services.synthesis_service import SynthesisService
    from app.schemas.retrieval import RetrievalQuery
    from app.repositories.project_repo import ResearchQuestionRepository

    q_repo = ResearchQuestionRepository(db)
    question = await q_repo.get_primary(project_id)
    question_text = question.question if question else "research topic"

    retrieval_svc = RetrievalService(db)
    result = await retrieval_svc.retrieve(
        RetrievalQuery(query=question_text, project_id=project_id, top_k=20, use_reranking=True)
    )
    snippets = [e.model_dump() for e in result.evidence]

    synthesis_svc = SynthesisService(db)
    synthesis = await synthesis_svc.synthesize(project_id, snippets)

    output = SynthesisOutput(synthesis=synthesis, evidence_count=len(snippets))
    logger.info("stage.synthesis.complete", project_id=ctx.project_id, evidence=len(snippets))
    return output


async def handle_gap_analysis(ctx: WorkflowContext, db: AsyncSession) -> GapAnalysisOutput:
    """Detect research gaps from synthesis output."""
    from app.services.gap_service import GapService

    project_id = uuid.UUID(ctx.project_id)
    synthesis_out: SynthesisOutput = ctx.stage_outputs.get(JobStage.SYNTHESIS.value)
    synthesis = synthesis_out.synthesis if synthesis_out else {}

    # Retrieve evidence snippets again for gap grounding
    from app.services.retrieval_service import RetrievalService
    from app.schemas.retrieval import RetrievalQuery
    from app.repositories.project_repo import ResearchQuestionRepository

    q_repo = ResearchQuestionRepository(db)
    question = await q_repo.get_primary(project_id)
    question_text = question.question if question else "research topic"

    retrieval_svc = RetrievalService(db)
    result = await retrieval_svc.retrieve(
        RetrievalQuery(query=question_text, project_id=project_id, top_k=20, use_reranking=False)
    )
    snippets = [e.model_dump() for e in result.evidence]

    gap_svc = GapService(db)
    gaps = await gap_svc.detect_gaps(project_id, synthesis, snippets)

    output = GapAnalysisOutput(gaps_detected=len(gaps))
    logger.info("stage.gap_analysis.complete", project_id=ctx.project_id, gaps=len(gaps))
    return output


async def handle_hypothesis(ctx: WorkflowContext, db: AsyncSession) -> HypothesisOutput:
    """Generate hypotheses for each detected gap."""
    from app.services.hypothesis_service import HypothesisService
    from app.repositories.research_repo import ResearchGapRepository

    project_id = uuid.UUID(ctx.project_id)
    gap_repo = ResearchGapRepository(db)
    gaps, _ = await gap_repo.list_by_project(project_id)

    hyp_svc = HypothesisService(db)
    total = 0
    for gap in gaps:
        hyps = await hyp_svc.generate_from_gap(project_id, gap.id)
        total += len(hyps)

    output = HypothesisOutput(hypotheses_generated=total)
    logger.info("stage.hypothesis.complete", project_id=ctx.project_id, hypotheses=total)
    return output


async def handle_experiment_design(
    ctx: WorkflowContext, db: AsyncSession
) -> ExperimentDesignOutput:
    """Design experiment specifications for each hypothesis."""
    from app.services.experiment_service import ExperimentService
    from app.repositories.research_repo import HypothesisRepository
    from app.models.research import HypothesisStatus

    project_id = uuid.UUID(ctx.project_id)
    hyp_repo = HypothesisRepository(db)
    hypotheses, _ = await hyp_repo.list_by_project(
        project_id, status=HypothesisStatus.DRAFT
    )

    exp_svc = ExperimentService(db)
    total = 0
    for hyp in hypotheses[:5]:  # cap at 5 to avoid excessive LLM calls
        try:
            await exp_svc.design_from_hypothesis(project_id, hyp.id)
            total += 1
        except Exception as exc:
            logger.warning(
                "stage.experiment_design.error",
                hypothesis_id=str(hyp.id),
                error=str(exc),
            )

    output = ExperimentDesignOutput(experiments_designed=total)
    logger.info(
        "stage.experiment_design.complete", project_id=ctx.project_id, experiments=total
    )
    return output


async def handle_verification(
    ctx: WorkflowContext, db: AsyncSession
) -> VerificationOutput:
    """Verify all claims in the project against stored evidence."""
    from app.services.verification_service import VerificationService
    from app.repositories.knowledge_repo import ClaimRepository

    project_id = uuid.UUID(ctx.project_id)
    verifier = VerificationService(db)
    summary = await verifier.verify_project_claims(project_id)

    claim_repo = ClaimRepository(db)
    unsupported = await claim_repo.get_unsupported_count(project_id)

    output = VerificationOutput(
        verification_summary=summary,
        unsupported_claims=unsupported,
    )
    logger.info(
        "stage.verification.complete",
        project_id=ctx.project_id,
        unsupported=unsupported,
    )
    return output


async def handle_reporting(ctx: WorkflowContext, db: AsyncSession) -> ReportingOutput:
    """Generate the full research report."""
    from app.services.report_service import ReportService
    from app.models.report import CitationStyle
    from app.schemas.report import ReportGenerateRequest

    project_id = uuid.UUID(ctx.project_id)
    report_svc = ReportService(db)

    report = await report_svc.generate(
        ReportGenerateRequest(
            project_id=project_id,
            citation_styles=[CitationStyle.APA, CitationStyle.BIBTEX],
            include_ablation=True,
            verify_claims=True,
        )
    )

    output = ReportingOutput(
        report_id=str(report.id),
        unsupported_claims=report.unsupported_claim_count,
    )
    logger.info(
        "stage.reporting.complete",
        project_id=ctx.project_id,
        report_id=str(report.id),
    )
    return output


# ── Dispatch table ─────────────────────────────────────────────────────────────
STAGE_HANDLERS = {
    JobStage.PLANNING:          handle_planning,
    JobStage.DISCOVERY:         handle_discovery,
    JobStage.INGESTION:         handle_ingestion,
    JobStage.ANALYSIS:          handle_analysis,
    JobStage.EXTRACTION:        handle_extraction,
    JobStage.SYNTHESIS:         handle_synthesis,
    JobStage.GAP_ANALYSIS:      handle_gap_analysis,
    JobStage.HYPOTHESIS:        handle_hypothesis,
    JobStage.EXPERIMENT_DESIGN: handle_experiment_design,
    JobStage.VERIFICATION:      handle_verification,
    JobStage.REPORTING:         handle_reporting,
}
