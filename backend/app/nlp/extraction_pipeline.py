"""
NLP extraction pipeline — runs on a processed paper.
Orchestrates: chunking → embedding → NER → relation extraction → keyphrase.
Persists all results to DB with full provenance.
"""
from __future__ import annotations

import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.knowledge import EntityType, RelationType
from app.nlp.chunker import TextChunk, chunk_sections
from app.nlp.embeddings import get_embedding_engine
from app.nlp.keyphrase import extract_keyphrases
from app.nlp.ner import extract_entities
from app.nlp.relations import extract_relations
from app.repositories.knowledge_repo import EntityRepository, RelationshipRepository
from app.repositories.paper_repo import PaperChunkRepository, PaperSectionRepository

logger = get_logger(__name__)


class ExtractionPipeline:
    """
    Full NLP extraction for a single paper.
    Input: paper sections (title, content, page_start)
    Output: chunks with embeddings + entities + relations stored in DB
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._chunks_repo = PaperChunkRepository(db)
        self._sections_repo = PaperSectionRepository(db)
        self._entities_repo = EntityRepository(db)
        self._relations_repo = RelationshipRepository(db)
        self._embedding_engine = get_embedding_engine()

    async def process_paper(
        self,
        paper_id: uuid.UUID,
        project_id: uuid.UUID,
        sections: List[dict],
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> dict:
        """
        Full extraction pipeline for a paper.
        Returns summary of what was extracted.
        """
        # Step 1 — persist sections
        section_records = []
        for i, sec in enumerate(sections):
            record = await self._sections_repo.create(
                paper_id=paper_id,
                title=sec.get("title"),
                content=sec.get("content", ""),
                section_type=sec.get("section_type"),
                page_start=sec.get("page_start"),
                page_end=sec.get("page_end"),
                position=i,
            )
            section_records.append((record, sec))

        # Step 2 — chunk all sections
        text_chunks = chunk_sections(sections, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Step 3 — compute embeddings in batch
        texts = [c.content for c in text_chunks]
        embeddings = await self._embedding_engine.encode(texts, batch_size=32)

        # Step 4 — persist chunks with embeddings
        chunk_records = []
        for chunk, embedding in zip(text_chunks, embeddings):
            section_id = None
            # Find matching section record by position
            for rec, sec in section_records:
                if rec.title == chunk.section_title:
                    section_id = rec.id
                    break

            record = await self._chunks_repo.create(
                paper_id=paper_id,
                section_id=section_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                embedding=embedding,
            )
            chunk_records.append((record, chunk))

        # Step 5 — NER + relations on full section text
        total_entities = 0
        total_relations = 0

        for chunk_record, chunk in chunk_records[:50]:  # cap to avoid DB flood
            # NER
            raw_entities = extract_entities(chunk.content, str(chunk_record.id))
            entity_records = []
            for ent in raw_entities:
                try:
                    entity_record = await self._entities_repo.create(
                        paper_id=paper_id,
                        project_id=project_id,
                        chunk_id=chunk_record.id,
                        name=ent.name,
                        canonical_name=ent.name.lower().strip(),
                        entity_type=ent.entity_type,
                        confidence=ent.confidence,
                        start_char=ent.start_char,
                        end_char=ent.end_char,
                        context_snippet=ent.context_snippet,
                    )
                    entity_records.append((entity_record, ent))
                    total_entities += 1
                except Exception as exc:
                    logger.warning("extraction.entity_persist_error", error=str(exc))

            # Relations
            if len(entity_records) >= 2:
                ner_ents = [ent for _, ent in entity_records]
                raw_relations = extract_relations(chunk.content, ner_ents)
                for rel in raw_relations:
                    # Resolve entity IDs
                    source_id = next(
                        (r.id for r, e in entity_records if e.name == rel.source_name), None
                    )
                    target_id = next(
                        (r.id for r, e in entity_records if e.name == rel.target_name), None
                    )
                    if source_id and target_id:
                        try:
                            await self._relations_repo.create(
                                project_id=project_id,
                                source_entity_id=source_id,
                                target_entity_id=target_id,
                                relation_type=rel.relation_type,
                                confidence=rel.confidence,
                                paper_id=paper_id,
                                chunk_id=chunk_record.id,
                                evidence_snippet=rel.evidence_snippet,
                            )
                            total_relations += 1
                        except Exception as exc:
                            logger.warning("extraction.relation_persist_error", error=str(exc))

        # Step 6 — keyphrases (store in paper metadata, not a separate table)
        full_text = " ".join(sec.get("content", "") for sec in sections)
        keyphrases = extract_keyphrases(full_text[:5000], top_n=15)

        logger.info(
            "extraction.complete",
            paper_id=str(paper_id),
            chunks=len(chunk_records),
            entities=total_entities,
            relations=total_relations,
        )

        return {
            "chunks": len(chunk_records),
            "entities": total_entities,
            "relations": total_relations,
            "keyphrases": [kp for kp, _ in keyphrases],
        }
