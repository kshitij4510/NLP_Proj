"""
Claim verification service.
Every claim is checked against stored evidence — never fabricated.
Verification states follow spec §3 Evidence Layer:
  SUPPORTED | PARTIALLY_SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE
"""
from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.knowledge import ArtifactType, Claim, VerificationStatus
from app.repositories.knowledge_repo import ClaimRepository, ClaimEvidenceRepository
from app.repositories.paper_repo import PaperChunkRepository

logger = get_logger(__name__)

VERIFICATION_PROMPT = """You are a claim verifier. Determine if the claim is supported by the evidence.

Claim: {claim}

Evidence:
{evidence}

Respond with JSON:
{{
  "status": "SUPPORTED" | "PARTIALLY_SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "supporting_snippet_indices": [list of evidence indices that support],
  "contradicting_snippet_indices": [list of evidence indices that contradict]
}}
"""


class VerificationService:
    def __init__(self, db: AsyncSession) -> None:
        self._claims = ClaimRepository(db)
        self._evidence = ClaimEvidenceRepository(db)
        self._chunks = PaperChunkRepository(db)

    async def verify_claim(
        self,
        claim_id: uuid.UUID,
        evidence_snippets: List[dict],
    ) -> Claim:
        """
        Verify a single claim against evidence snippets.
        Updates the claim's verification_status and confidence.
        """
        from app.services.llm_service import LLMService

        claim = await self._claims.get_or_raise(claim_id)
        evidence_text = self._format_evidence(evidence_snippets)
        prompt = VERIFICATION_PROMPT.format(
            claim=claim.claim_text, evidence=evidence_text
        )

        llm = LLMService()
        result = await llm.generate_json(prompt)

        status = self._parse_status(result.get("status", "INSUFFICIENT_EVIDENCE"))
        confidence = float(result.get("confidence", 0.0))

        updated = await self._claims.update(
            claim_id,
            verification_status=status,
            confidence=confidence,
            artifact_type=self._derive_artifact_type(status),
            attributes={
                **(claim.attributes or {}),
                "verification_reasoning": result.get("reasoning", ""),
            },
        )

        logger.info(
            "claim.verified",
            claim_id=str(claim_id),
            status=status.value,
            confidence=confidence,
        )
        return updated  # type: ignore[return-value]

    async def verify_project_claims(
        self, project_id: uuid.UUID
    ) -> Dict[str, int]:
        """
        Verify all pending claims in a project.
        Returns summary counts per verification status.
        """
        claims, _ = await self._claims.list_by_project(project_id)
        summary: Dict[str, int] = {s.value: 0 for s in VerificationStatus}

        for claim in claims:
            # Retrieve supporting evidence for this claim
            evidence_links = await self._evidence.list_by_claim(claim.id)
            if not evidence_links:
                await self._claims.update(
                    claim.id,
                    verification_status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                )
                summary[VerificationStatus.INSUFFICIENT_EVIDENCE.value] += 1
                continue

            # Build snippet context from linked chunks
            chunk_ids = [e.chunk_id for e in evidence_links if e.chunk_id]
            chunks = await self._chunks.get_chunks_by_ids(chunk_ids)
            snippets = [
                {"content": c.content, "page_number": c.page_number, "paper_id": str(c.paper_id)}
                for c in chunks
            ]
            updated = await self.verify_claim(claim.id, snippets)
            summary[updated.verification_status.value] += 1

        logger.info(
            "verification.project_complete",
            project_id=str(project_id),
            summary=summary,
        )
        return summary

    @staticmethod
    def _format_evidence(snippets: List[dict]) -> str:
        parts = []
        for i, s in enumerate(snippets[:15]):
            parts.append(f"[{i+1}] {s.get('content', '')[:500]}")
        return "\n".join(parts)

    @staticmethod
    def _parse_status(raw: str) -> VerificationStatus:
        mapping = {s.value: s for s in VerificationStatus}
        return mapping.get(raw.upper(), VerificationStatus.INSUFFICIENT_EVIDENCE)

    @staticmethod
    def _derive_artifact_type(status: VerificationStatus) -> ArtifactType:
        if status == VerificationStatus.SUPPORTED:
            return ArtifactType.EVIDENCE
        if status == VerificationStatus.PARTIALLY_SUPPORTED:
            return ArtifactType.INTERPRETATION
        if status == VerificationStatus.CONTRADICTED:
            return ArtifactType.UNSUPPORTED_CLAIM
        return ArtifactType.UNSUPPORTED_CLAIM
