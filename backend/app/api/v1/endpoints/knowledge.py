"""Knowledge graph — entities, relationships, claims endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, APIRouter, Query

from app.api.deps import CurrentUser, DB, require_project_access
from app.models.knowledge import EntityType, RelationType, VerificationStatus
from app.schemas.common import PaginatedResponse
from app.repositories.knowledge_repo import (
    ClaimRepository, EntityRepository, RelationshipRepository,
)

router = APIRouter(prefix="/projects/{project_id}/knowledge", tags=["knowledge"], dependencies=[Depends(require_project_access)])


@router.get("/entities", response_model=dict)
async def list_entities(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    entity_type: Optional[EntityType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
):
    repo = EntityRepository(db)
    offset = (page - 1) * page_size
    items, total = await repo.list_by_project(
        project_id, entity_type=entity_type, offset=offset, limit=page_size
    )
    return {
        "items": [
            {
                "id": str(e.id),
                "name": e.name,
                "entity_type": e.entity_type.value,
                "confidence": e.confidence,
                "paper_id": str(e.paper_id),
            }
            for e in items
        ],
        "total": total,
        "page": page,
    }


@router.get("/entities/distribution", response_model=dict)
async def entity_type_distribution(project_id: uuid.UUID, user: CurrentUser, db: DB):
    repo = EntityRepository(db)
    dist = await repo.get_type_distribution(project_id)
    return {"distribution": {t.value: count for t, count in dist}}


@router.get("/relationships", response_model=dict)
async def list_relationships(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    relation_type: Optional[RelationType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
):
    repo = RelationshipRepository(db)
    offset = (page - 1) * page_size
    items, total = await repo.list_by_project(
        project_id, relation_type=relation_type, offset=offset, limit=page_size
    )
    return {
        "items": [
            {
                "id": str(r.id),
                "source": r.source_entity.name if r.source_entity else None,
                "target": r.target_entity.name if r.target_entity else None,
                "relation_type": r.relation_type.value,
                "confidence": r.confidence,
                "evidence_snippet": r.evidence_snippet,
            }
            for r in items
        ],
        "total": total,
    }


@router.get("/claims", response_model=dict)
async def list_claims(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    verification_status: Optional[VerificationStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
):
    repo = ClaimRepository(db)
    offset = (page - 1) * page_size
    items, total = await repo.list_by_project(
        project_id,
        verification_status=verification_status,
        offset=offset,
        limit=page_size,
    )
    return {
        "items": [
            {
                "id": str(c.id),
                "claim_text": c.claim_text,
                "paper_id": str(c.paper_id) if c.paper_id else None,
                "evidence_links": [{"id": str(e.id), "section_title": "Source passage", "relevance_score": e.relevance_score, "paper_id": str(e.paper_id), "chunk_id": str(e.chunk_id) if e.chunk_id else None,
                    "page_number": e.page_number, "evidence_snippet": e.evidence_snippet, "support_type": e.support_type.value} for e in c.evidence_links],
                "verification_status": c.verification_status.value,
                "artifact_type": c.artifact_type.value,
                "confidence": c.confidence,
            }
            for c in items
        ],
        "total": total,
    }
