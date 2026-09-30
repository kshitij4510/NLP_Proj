"""
Entity, Relationship, Claim, ClaimEvidence repositories.
Enforces evidence provenance — claims must always link to real chunks.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from app.models.knowledge import (
    ArtifactType, Claim, ClaimEvidence, Entity, EntityType,
    Relationship, RelationType, VerificationStatus,
)
from app.repositories.base import BaseRepository


class EntityRepository(BaseRepository[Entity]):
    model_class = Entity

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        entity_type: Optional[EntityType] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Entity], int]:
        return await self.list(
            project_id=project_id,
            **({"entity_type": entity_type} if entity_type else {}),
            offset=offset,
            limit=limit,
        )

    async def list_by_paper(
        self,
        paper_id: uuid.UUID,
        entity_type: Optional[EntityType] = None,
    ) -> List[Entity]:
        query = select(Entity).where(Entity.paper_id == paper_id)
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        result = await self.db.execute(query.order_by(Entity.entity_type))
        return list(result.scalars().all())

    async def find_by_canonical_name(
        self,
        project_id: uuid.UUID,
        canonical_name: str,
        entity_type: Optional[EntityType] = None,
    ) -> Optional[Entity]:
        query = select(Entity).where(
            and_(
                Entity.project_id == project_id,
                Entity.canonical_name == canonical_name,
            )
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_type_distribution(
        self, project_id: uuid.UUID
    ) -> List[Tuple[EntityType, int]]:
        result = await self.db.execute(
            select(Entity.entity_type, func.count(Entity.id).label("count"))
            .where(Entity.project_id == project_id)
            .group_by(Entity.entity_type)
            .order_by(func.count(Entity.id).desc())
        )
        return [(row[0], row[1]) for row in result.all()]


class RelationshipRepository(BaseRepository[Relationship]):
    model_class = Relationship

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        relation_type: Optional[RelationType] = None,
        offset: int = 0,
        limit: int = 200,
    ) -> Tuple[List[Relationship], int]:
        query = (
            select(Relationship)
            .options(
                selectinload(Relationship.source_entity),
                selectinload(Relationship.target_entity),
            )
            .where(Relationship.project_id == project_id)
        )
        count_q = select(func.count()).select_from(Relationship).where(
            Relationship.project_id == project_id
        )
        if relation_type:
            query = query.where(Relationship.relation_type == relation_type)
            count_q = count_q.where(Relationship.relation_type == relation_type)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total

    async def get_entity_neighbors(
        self, entity_id: uuid.UUID, limit: int = 50
    ) -> List[Relationship]:
        result = await self.db.execute(
            select(Relationship)
            .options(
                selectinload(Relationship.source_entity),
                selectinload(Relationship.target_entity),
            )
            .where(
                (Relationship.source_entity_id == entity_id)
                | (Relationship.target_entity_id == entity_id)
            )
            .limit(limit)
        )
        return list(result.scalars().all())


class ClaimRepository(BaseRepository[Claim]):
    model_class = Claim

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        *,
        verification_status: Optional[VerificationStatus] = None,
        artifact_type: Optional[ArtifactType] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Claim], int]:
        query = (
            select(Claim)
            .options(selectinload(Claim.evidence_links))
            .where(Claim.project_id == project_id)
        )
        count_q = select(func.count()).select_from(Claim).where(
            Claim.project_id == project_id
        )
        if verification_status:
            query = query.where(Claim.verification_status == verification_status)
            count_q = count_q.where(Claim.verification_status == verification_status)
        if artifact_type:
            query = query.where(Claim.artifact_type == artifact_type)
            count_q = count_q.where(Claim.artifact_type == artifact_type)

        total = (await self.db.execute(count_q)).scalar_one()
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total

    async def get_unsupported_count(self, project_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Claim).where(
                and_(
                    Claim.project_id == project_id,
                    Claim.verification_status == VerificationStatus.INSUFFICIENT_EVIDENCE,
                )
            )
        )
        return result.scalar_one()

    async def list_with_evidence(self, project_id: uuid.UUID) -> List[Claim]:
        result = await self.db.execute(
            select(Claim)
            .options(selectinload(Claim.evidence_links))
            .where(Claim.project_id == project_id)
        )
        return list(result.scalars().all())


class ClaimEvidenceRepository(BaseRepository[ClaimEvidence]):
    model_class = ClaimEvidence

    async def list_by_claim(self, claim_id: uuid.UUID) -> List[ClaimEvidence]:
        result = await self.db.execute(
            select(ClaimEvidence)
            .where(ClaimEvidence.claim_id == claim_id)
            .order_by(ClaimEvidence.relevance_score.desc())
        )
        return list(result.scalars().all())

    async def list_by_paper(self, paper_id: uuid.UUID) -> List[ClaimEvidence]:
        result = await self.db.execute(
            select(ClaimEvidence).where(ClaimEvidence.paper_id == paper_id)
        )
        return list(result.scalars().all())
