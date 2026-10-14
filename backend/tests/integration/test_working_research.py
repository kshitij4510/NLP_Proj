"""Exercise real local workflow stages and user-facing APIs, including persisted artifacts."""
import uuid
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.project import ResearchProject, ResearchQuestion
from app.models.paper import Paper, PaperStatus
from app.models.job import ResearchJob, JobStage, JobStatus
from app.repositories.job_repo import JobRepository
from app.repositories.paper_repo import PaperRepository, PaperChunkRepository
from app.repositories.report_repo import ReportRepository
from app.repositories.knowledge_repo import ClaimRepository
from app.repositories.experiment_repo import ExperimentRepository
from app.agents.workflow_runner import WorkflowRunner
from app.schemas.paper import PaperSearchResult
from app.schemas.retrieval import RetrievalQuery
from app.services.retrieval_service import RetrievalService
from app.nlp.embeddings import EmbeddingEngine


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "demo")
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "lexical-hash")
    monkeypatch.setattr(EmbeddingEngine, "_instance", None)
    from app.ingestion import local_corpus
    records = [PaperSearchResult(title="Retrieval grounding for hallucination detection", abstract="Retrieval improves evidence grounding in language models. However, retrieval remains limited by noisy passages in question answering.", authors=["A Researcher"], year=2024, venue="Test fixture", doi="10.test/grounding", arxiv_id=None, pdf_url=None, citation_count=0, source="test_fixture", relevance_score=None, external_id="test:1"),
        PaperSearchResult(title="Evaluating factuality in language generation", abstract="We evaluate factuality and hallucination detection using F1 and precision on TruthfulQA. The method provides traceable evaluation of generated responses.", authors=["B Researcher"], year=2024, venue="Test fixture", doi="10.test/factuality", arxiv_id=None, pdf_url=None, citation_count=0, source="test_fixture", relevance_score=None, external_id="test:2")]
    monkeypatch.setattr(local_corpus, "search_corpus", lambda *args, **kwargs: records)
    return records


async def setup_project(db):
    user = User(email="workflow@example.com", username="workflow", hashed_password="unused")
    db.add(user); await db.flush()
    project = ResearchProject(owner_id=user.id, title="Hallucination research")
    db.add(project); await db.flush()
    db.add(ResearchQuestion(project_id=project.id, question="How does retrieval reduce hallucination?", is_primary=True))
    await db.commit()
    return project


@pytest.mark.asyncio
async def test_local_pipeline_persists_every_stage_and_report(db, monkeypatch, offline):
    project = await setup_project(db)
    job = await JobRepository(db).create(project_id=project.id, stage=JobStage.PLANNING, status=JobStatus.PENDING)
    await db.commit()
    import app.database.session
    monkeypatch.setattr(app.database.session, "AsyncSessionLocal", async_sessionmaker(db.bind, expire_on_commit=False))
    from app.workers.local import _execute
    await _execute(project.id, job.id, JobStage.PLANNING, "pipeline", {})
    await db.refresh(job)
    assert job.status == JobStatus.COMPLETED, job.error_message
    assert job.stage == JobStage.COMPLETED and job.progress == 1
    assert len(job.job_metadata["stage_outputs"]) == 11
    papers, count = await PaperRepository(db).list_by_project(project.id)
    assert count == 2 and all(p.status == PaperStatus.PROCESSED for p in papers)
    assert await PaperChunkRepository(db).count() == 2
    claims, count = await ClaimRepository(db).list_by_project(project.id)
    assert count == 2 and all(c.evidence_links for c in claims)
    reports, count = await ReportRepository(db).list_by_project(project.id)
    assert count == 1
    experiments, count = await ExperimentRepository(db).list_by_project(project.id)
    assert count >= 1 and experiments[0].model_spec
    # A second run reuses source papers, extracted chunks, hypotheses, and experiment designs.
    other = await JobRepository(db).create(project_id=project.id, stage=JobStage.PLANNING, status=JobStatus.PENDING)
    await db.commit()
    await _execute(project.id, other.id, JobStage.PLANNING, "pipeline", {})
    await db.refresh(other)
    assert other.status == JobStatus.COMPLETED, other.error_message
    assert (await PaperRepository(db).list_by_project(project.id))[1] == 2
    assert await PaperChunkRepository(db).count() == 2


@pytest.mark.asyncio
async def test_failed_local_job_has_terminal_state(db, monkeypatch, offline):
    project = await setup_project(db)
    job = await JobRepository(db).create(project_id=project.id, stage=JobStage.PLANNING, status=JobStatus.PENDING)
    await db.commit()
    monkeypatch.setattr(settings, "JOB_MAX_RETRIES", 0)
    from app.agents.stage_handlers import STAGE_HANDLERS
    async def broken_handler(ctx, session):
        raise RuntimeError("Source unavailable")
    monkeypatch.setitem(STAGE_HANDLERS, JobStage.PLANNING, broken_handler)
    import app.database.session
    monkeypatch.setattr(app.database.session, "AsyncSessionLocal", async_sessionmaker(db.bind, expire_on_commit=False))
    from app.workers.local import _execute
    await _execute(project.id, job.id, JobStage.PLANNING, "pipeline", {})
    await db.refresh(job)
    assert job.status == JobStatus.FAILED
    assert "Source unavailable" in job.error_message


@pytest.mark.asyncio
async def test_paper_search_is_scoped_before_ranking(db, offline):
    project = await setup_project(db)
    from app.services.paper_service import PaperService
    from app.ingestion.ingestion_pipeline import IngestionPipeline
    await PaperService(db).ingest_from_search_results(project.id, offline)
    await IngestionPipeline(db).run_ingestion(project.id, batch_size=20)
    papers, _ = await PaperRepository(db).list_by_project(project.id)
    selected = next(p for p in papers if "factuality" in p.title)
    result = await RetrievalService(db).retrieve(RetrievalQuery(project_id=project.id, query="hallucination factuality", metadata_filters={"paper_id": str(selected.id)}, use_reranking=True))
    assert result.evidence and all(e.paper_id == selected.id for e in result.evidence)
    assert result.reranked is False


@pytest.mark.asyncio
async def test_discovery_graph_evidence_and_experiment_tracking_api(client, sample_user_data, offline):
    await client.post("/api/v1/auth/register", json=sample_user_data)
    tokens = (await client.post("/api/v1/auth/login", json={"email": sample_user_data["email"], "password": sample_user_data["password"]})).json()
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    project = (await client.post("/api/v1/projects", headers=headers, json={"title": "Research corpus"})).json()
    base = f"/api/v1/projects/{project['id']}"
    for _ in range(2):
        response = await client.post(base + "/papers/discover/search", headers=headers, json={"query": "retrieval hallucination"})
        assert response.status_code == 200, response.text
    response = await client.get(base + "/papers", headers=headers)
    assert response.json()["total"] == 2
    response = await client.get(base + "/knowledge/entities/distribution", headers=headers)
    assert response.status_code == 200 and response.json()["distribution"]
    response = await client.get(base + "/knowledge/claims", headers=headers)
    assert response.json()["items"][0]["evidence_links"][0]["evidence_snippet"]
    experiment = (await client.post(base + "/experiments", headers=headers, json={"title": "Recorded retrieval evaluation", "model_spec": {"architecture": "BM25"}})).json()
    response = await client.post(base + f"/experiments/{experiment['id']}/runs", headers=headers, json={"metrics": {"recall": 0.8}, "git_commit": "abcdef"})
    assert response.status_code == 201, response.text
    response = await client.get(base + f"/experiments/{experiment['id']}", headers=headers)
    assert response.json()["status"] == "completed"
    response = await client.post(base + "/research/pipeline/run?stage=INVALID", headers=headers)
    assert response.status_code == 422
