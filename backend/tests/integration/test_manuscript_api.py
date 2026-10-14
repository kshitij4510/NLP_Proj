import io, zipfile
import pytest
from app.core.config import settings

async def login_project(client, sample_user_data):
    await client.post("/api/v1/auth/register",json=sample_user_data)
    token=(await client.post("/api/v1/auth/login",json={"email":sample_user_data["email"],"password":sample_user_data["password"]})).json()["access_token"]
    client.headers["Authorization"]="Bearer "+token
    response=await client.post("/api/v1/projects",json={"title":"Source-specific research"})
    assert response.status_code==201,response.text
    return response.json()["id"]

@pytest.mark.asyncio
async def test_project_source_and_all_exports(client,sample_user_data,monkeypatch):
    monkeypatch.setattr(settings,"LLM_PROVIDER","demo")
    project=await login_project(client,sample_user_data)
    source="# Retrieval project\nWe implement a BM25 retriever for scientific document search. However, the method fails on cross-lingual queries and sparse corpora. The system uses a local index and returns matching document passages."
    response=await client.post(f"/api/v1/projects/{project}/manuscripts",files={"file":("README.md",source,"text/markdown")},data={"title":"Retrieval study"})
    assert response.status_code==200,response.text
    data=response.json();assert data["gaps"] and "cross-lingual" in data["gaps"][0]["evidence"]
    assert "No new experiments" in data["report"]["results"]
    for fmt,marker in [("ieee",r"\documentclass[conference]{IEEEtran}"),("markdown","# Retrieval study"),("bibtex","% No verified references")]:
        export=await client.get(f"/api/v1/projects/{project}/reports/{data['report']['id']}/export/{fmt}")
        assert export.status_code==200 and marker in export.text
        assert "attachment" in export.headers["content-disposition"]
    bad=await client.post(f"/api/v1/projects/{project}/manuscripts",data={"github_url":"http://localhost/private"})
    assert bad.status_code==422

@pytest.mark.asyncio
async def test_pdf_review_preserves_source_and_bibliography(client,sample_user_data,monkeypatch,tmp_path):
    import fitz
    monkeypatch.setattr(settings,"LLM_PROVIDER","demo")
    monkeypatch.setattr(settings,"EMBEDDING_MODEL","lexical-hash")
    monkeypatch.setattr(settings,"UPLOAD_DIR",str(tmp_path))
    from app.nlp.embeddings import EmbeddingEngine
    monkeypatch.setattr(EmbeddingEngine,"_instance",None)
    project=await login_project(client,sample_user_data)
    document=fitz.open();page=document.new_page()
    source="Retrieval evaluation study\nAbstract\nWe study retrieval grounding in language models.\nLimitations\nHowever, the system fails on multilingual document retrieval.\nMethods\nWe use BM25 to rank passages and evaluate precision on a held-out test set."
    page.insert_text((50,50),source);payload=document.tobytes();document.close()
    response=await client.post(f"/api/v1/projects/{project}/manuscripts",files={"file":("study.pdf",payload,"application/pdf")})
    assert response.status_code==200,response.text
    data=response.json();assert data["gaps"]
    assert "Original paper content" in data["report"]["method_comparison"]
    assert "multilingual" in data["report"]["method_comparison"]
    bib=await client.get(f"/api/v1/projects/{project}/reports/{data['report']['id']}/export/bibtex")
    assert bib.status_code==200 and "@misc{" in bib.text
    about=await client.get("/api/v1/about/papers")
    assert about.status_code==200 and about.json()["total"]==1
    ieee=await client.get(f"/api/v1/projects/{project}/reports/{data['report']['id']}/export/ieee")
    assert r"\bibitem{ref1}" in ieee.text and "multilingual" in ieee.text

@pytest.mark.asyncio
async def test_public_github_archive_inspection(client,sample_user_data,monkeypatch):
    import types, httpx
    from app.api.v1.endpoints import manuscripts
    monkeypatch.setattr(settings,"LLM_PROVIDER","demo")
    project=await login_project(client,sample_user_data)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        z.writestr("repo/README.md","A retrieval project that indexes scientific abstracts. However, the implementation lacks multilingual support and needs stronger evaluation. We rank documents with BM25 and return original passages.")
    class Meta:
        status_code=200
        def json(self): return {"default_branch":"main"}
    class Response:
        status_code=200
        async def aiter_bytes(self): yield stream.getvalue()
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
    class Remote:
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def get(self,url):
            assert url=="https://api.github.com/repos/example/retrieval"
            return Meta()
        def stream(self,method,url):
            assert url=="https://codeload.github.com/example/retrieval/zip/refs/heads/main"
            return Response()
    monkeypatch.setattr(manuscripts,"httpx",types.SimpleNamespace(AsyncClient=lambda **kwargs:Remote(),HTTPError=httpx.HTTPError))
    response=await client.post(f"/api/v1/projects/{project}/manuscripts",data={"github_url":"https://github.com/example/retrieval"})
    assert response.status_code==200,response.text
    assert response.json()["source"]=="https://github.com/example/retrieval"
    assert "multilingual" in response.json()["gaps"][0]["evidence"]
