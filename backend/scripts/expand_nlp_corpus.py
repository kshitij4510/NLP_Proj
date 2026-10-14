"""Fetch official ACL metadata, cache 120 NLP papers, and index the local research corpus."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
import urllib.request
import xml.etree.ElementTree as ET

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
import local_main
from app.database.session import AsyncSessionLocal, engine
from app.models.base import Base
from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository
from app.repositories.paper_repo import PaperRepository
from app.services.paper_service import PaperService
from app.ingestion.ingestion_pipeline import IngestionPipeline
from app.schemas.paper import PaperSearchResult


def text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def fetch():
    papers = []
    sources = []
    for collection in ["2024.acl", "2024.emnlp"]:
        url = f"https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml/{collection}.xml"
        with urllib.request.urlopen(url, timeout=60) as response:
            document = ET.fromstring(response.read())
        sources.append(url)
        for volume in document.findall("volume"):
            venue = text(volume.find("meta/booktitle")) or collection
            year = int(text(volume.find("meta/year")) or collection[:4])
            for paper in volume.findall("paper"):
                title = text(paper.find("title"))
                abstract = text(paper.find("abstract"))
                if not title or not abstract or paper.get("id") == "0":
                    continue
                identifier = collection + "-" + volume.get("id") + "." + paper.get("id")
                url = "https://aclanthology.org/" + identifier + "/"
                authors = [" ".join(filter(None, [text(a.find("first")), text(a.find("last"))])) for a in paper.findall("author")]
                title_lower = title.lower()
                priority = sum(term in title_lower for term in ["hallucinat", "retrieval", "factual", "faithful", "rag", "verification"])
                papers.append((priority, {"title": title, "abstract": abstract, "authors": authors,
                    "year": year, "venue": venue, "doi": text(paper.find("doi")) or None,
                    "arxiv_id": None, "pdf_url": "https://aclanthology.org/" + identifier + ".pdf",
                    "citation_count": 0, "source": "acl_anthology", "relevance_score": None, "external_id": url}))
    papers.sort(key=lambda pair: pair[0], reverse=True)
    unique = {entry["external_id"]: entry for _, entry in papers}
    selected = list(unique.values())[:120]
    if len(selected) < 80:
        raise RuntimeError("Insufficient official metadata retrieved")
    path = ROOT / "data" / "nlp_corpus.json"
    path.write_text(json.dumps({"retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources, "scope": "120 selected ACL/EMNLP 2024 NLP abstracts, prioritizing retrieval and hallucination research; not an exhaustive review.",
        "papers": selected}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Cached {len(selected)} official NLP paper records")
    return selected


async def seed(records):
    database = BACKEND / "researchmind_local.db"
    if database.exists():
        backup_path = database.with_name("researchmind_local.before_pipeline_repair_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db")
        with sqlite3.connect(database) as source, sqlite3.connect(backup_path) as backup:
            source.backup(backup)
        print("Database backup:", backup_path.name)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        researcher = await UserRepository(db).get_by_email("researcher@example.com")
        demo = await UserRepository(db).get_by_email("demo@researchmind.ai")
        if not researcher:
            raise RuntimeError("Create the local researcher account before seeding")
        if demo:
            projects, _ = await ProjectRepository(db).list_by_owner(demo.id, limit=100)
            for project in projects:
                if project.title in ["Hallucination Detection and Mitigation in Retrieval-Augmented Generation", "Transformer Architectures in NLP"]:
                    await ProjectRepository(db).update(project.id, owner_id=researcher.id)
        projects, _ = await ProjectRepository(db).list_by_owner(researcher.id, limit=100)
        target = next((p for p in projects if "Hallucination" in p.title), None)
        if not target:
            raise RuntimeError("Research workspace not found")
        added, skipped = await PaperService(db).ingest_from_search_results(target.id, [PaperSearchResult(**r) for r in records])
        await db.commit()
        result = await IngestionPipeline(db).run_ingestion(target.id, batch_size=200)
        await db.commit()
        # Recompute old seed vectors using the configured lexical space.
        from app.models.paper import PaperChunk, Paper
        from sqlalchemy import select
        from app.nlp.embeddings import get_embedding_engine
        from app.repositories.paper_repo import PaperChunkRepository
        chunks = list((await db.execute(select(PaperChunk).join(Paper).where(Paper.project_id == target.id))).scalars())
        embeddings = await get_embedding_engine().encode([c.content for c in chunks])
        await PaperChunkRepository(db).bulk_update_embeddings([(c.id, e) for c, e in zip(chunks, embeddings)])
        await db.commit()
        _, total = await PaperRepository(db).list_by_project(target.id, limit=1)
        print(json.dumps({"project_id": str(target.id), "papers": total, "added": added, "duplicates_skipped": skipped, "indexing": result, "chunks": len(chunks)}))
    await engine.dispose()

if __name__ == "__main__":
    if "--cached" in sys.argv:
        records = json.loads((ROOT / "data" / "nlp_corpus.json").read_text(encoding="utf-8"))["papers"]
    else:
        records = fetch()
    asyncio.run(seed(records))
