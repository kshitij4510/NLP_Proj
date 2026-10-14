"""End-to-end check of the isolated production stack. Uses explicit test fixtures."""
import json, secrets, time, uuid
from pathlib import Path
import httpx, fitz
base="http://127.0.0.1:18081/api/v1"
out=Path(__file__).resolve().parents[2]/"examples"/"verification"
def checked(response):
    if response.is_error: raise RuntimeError(f"HTTP {response.status_code} at {response.request.url}: {response.text[:700]}")
    return response
with httpx.Client(timeout=180) as c:
    for url in ("http://127.0.0.1:18000/health","http://127.0.0.1:18080/","http://127.0.0.1:18081/health","http://127.0.0.1:18081/"):
        checked(c.get(url))
    print("Production routes passed",flush=True)
    suffix=uuid.uuid4().hex[:10]; email=f"verify_{suffix}@example.com"; password="Verify1"+secrets.token_hex(12)
    checked(c.post(base+"/auth/register",json={"email":email,"username":"verify_"+suffix,"password":password}))
    tokens=checked(c.post(base+"/auth/login",json={"email":email,"password":password})).json()
    c.headers["Authorization"]="Bearer "+tokens["access_token"]
    project=checked(c.post(base+"/projects",json={"title":"Production verification fixture","research_question":{"question":"How can retrieval improve grounded language generation?"}})).json()["id"]
    doc=fitz.open(); page=doc.new_page()
    page.insert_textbox((50,50,550,750),"PRODUCTION VERIFICATION FIXTURE\n\nAbstract\nWe inspect retrieval grounding in generated language. This is synthetic test input, not published research or measured evidence.\n\nMethods\nA BM25 retriever ranks scientific passages for question answering. We compare retrieval variants on held-out queries using precision and recall.\n\nLimitations\nHowever, retrieval remains limited by noisy evidence passages and multilingual query coverage. Future work should evaluate retrieval consistency under contradictory source documents.\n\nConclusion\nA reproducible evaluation needs named baselines, random seeds, and component ablations.")
    payload=doc.tobytes();doc.close()
    review=checked(c.post(base+f"/projects/{project}/manuscripts",files={"file":("verification.pdf",payload,"application/pdf")},data={"title":"Production verification fixture"})).json()
    assert review["gaps"],"No source gaps returned"
    print("PDF ingestion and revision passed",flush=True)
    result=checked(c.post(base+"/retrieval/search",json={"project_id":project,"query":"retrieval grounded language evidence","top_k":5})).json()
    assert result["evidence"],"No retrieved evidence"
    assert result["dense_candidates"] > 0,"PostgreSQL vector search returned no candidates"
    print("PostgreSQL hybrid/vector retrieval passed",flush=True)
    job=checked(c.post(base+f"/projects/{project}/research/pipeline/run",params={"stage":"INGESTION"})).json()["job_id"]
    for i in range(120):
        status=checked(c.get(base+f"/projects/{project}/jobs/{job}")).json()
        if status["status"] in ("completed","failed","cancelled"): break
        if i%10==0: print("Worker stage: "+status["stage"],flush=True)
        time.sleep(2)
    assert status["status"]=="completed",status.get("error_message") or status
    print("Redis/ARQ pipeline passed",flush=True)
    reports=checked(c.get(base+f"/projects/{project}/reports")).json()["items"]
    assert len(reports)>=2,"Pipeline did not persist a report"
    for fmt,ext in [("ieee","tex"),("markdown","md"),("bibtex","bib")]:
        exported=checked(c.get(base+f"/projects/{project}/reports/{reports[0]['id']}/export/{fmt}"))
        assert len(exported.content)>50
        (out/("production_fixture."+ext)).write_text(exported.text,encoding="utf-8")
    checked(c.get(base+f"/projects/{project}/knowledge/entities/distribution"))
    assert checked(c.get(base+"/about/papers")).json()["total"]>=1
    (out/"production-results.json").write_text(json.dumps({"routes":True,"pdf_ingestion":True,"hybrid_retrieval":True,"arq_pipeline":status["status"],"reports":len(reports),"exports":["ieee","markdown","bibtex"],"fixture_project":project},indent=2),encoding="utf-8")
    print("All production workflow checks passed",flush=True)
