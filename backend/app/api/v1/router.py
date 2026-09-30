"""API v1 router — assembles all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, projects, papers, retrieval, research,
    experiments, reports, jobs, knowledge,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(papers.router)
api_router.include_router(retrieval.router)
api_router.include_router(research.router)
api_router.include_router(experiments.router)
api_router.include_router(reports.router)
api_router.include_router(jobs.router)
api_router.include_router(knowledge.router)
