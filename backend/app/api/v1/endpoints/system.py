from fastapi import APIRouter
from app.api.deps import CurrentUser
from app.core.config import settings
router = APIRouter(prefix="/system", tags=["system"])
@router.get("/runtime")
async def runtime(user: CurrentUser):
    return {"database": "SQLite" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL",
        "worker": "In-process asyncio" if settings.DATABASE_URL.startswith("sqlite") else "ARQ / Redis",
        "llm_provider": settings.LLM_PROVIDER, "embedding_model": settings.EMBEDDING_MODEL,
        "dense_weight": settings.HYBRID_ALPHA, "status": "online"}
