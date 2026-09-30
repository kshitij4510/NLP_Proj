"""Retrieval and search endpoints."""
from fastapi import APIRouter
from app.api.deps import CurrentUser, DB
from app.schemas.retrieval import RetrievalQuery, RetrievalResult
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResult)
async def search(query: RetrievalQuery, user: CurrentUser, db: DB):
    """
    Hybrid BM25 + dense retrieval with optional reranking.
    Returns evidence snippets with full provenance (paper, page, section, scores).
    """
    svc = RetrievalService(db)
    return await svc.retrieve(query)
