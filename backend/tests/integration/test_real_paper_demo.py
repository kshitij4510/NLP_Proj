"""Optional end-to-end check using the downloaded official RAG paper."""
from pathlib import Path
import pytest
from app.core.config import settings
from app.nlp.embeddings import EmbeddingEngine
from tests.integration.test_manuscript_api import login_project


@pytest.mark.asyncio
async def test_official_rag_paper_review_search_and_exports(client, sample_user_data, monkeypatch, tmp_path):
    source = Path(__file__).resolve().parents[3] / "data/demo-papers/lewis_2020_rag.pdf"
    if not source.exists():
        pytest.skip("Optional official paper has not been downloaded")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "demo")
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "lexical-hash")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(EmbeddingEngine, "_instance", None)
    project = await login_project(client, sample_user_data)
    result = await client.post(f"/api/v1/projects/{project}/manuscripts", files={"file": (source.name, source.read_bytes(), "application/pdf")}, data={"title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"})
    assert result.status_code == 200, result.text
    report = result.json()["report"]
    checks = {check["topic"]: check for check in result.json()["review_checks"]}
    assert checks["Ablation"]["status"] == "mention located"
    assert checks["Ablation"]["page"] == 7
    assert checks["Reproducibility"]["status"] == "mention located"
    findings = result.json()["gaps"]
    assert all(f["page"] and f["evidence"].endswith(".") for f in findings)
    assert not any("their ability to access" in f["evidence"] for f in findings)
    assert any("jointly pre-trained from scratch" in f["evidence"] and f["kind"] == "author-stated future work" for f in findings)
    assert "Original paper content" in report["method_comparison"]
    assert "Wikipedia" in report["method_comparison"]
    search = await client.post("/api/v1/retrieval/search", json={"project_id": project, "query": "retrieval augmented generation Wikipedia", "top_k": 5, "use_reranking": False})
    assert search.status_code == 200, search.text
    assert search.json()["evidence"]
    for fmt in ("ieee", "markdown", "bibtex"):
        export = await client.get(f"/api/v1/projects/{project}/reports/{report['id']}/export/{fmt}")
        assert export.status_code == 200, export.text
        assert export.content
