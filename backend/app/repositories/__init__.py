"""
ResearchMind repository layer.
One repository class per domain aggregate.
"""
from app.repositories.base import BaseRepository
from app.repositories.user_repo import UserRepository
from app.repositories.project_repo import ProjectRepository, ResearchQuestionRepository
from app.repositories.paper_repo import (
    PaperRepository, PaperChunkRepository, PaperSectionRepository, PaperAuthorRepository,
)
from app.repositories.knowledge_repo import (
    EntityRepository, RelationshipRepository, ClaimRepository, ClaimEvidenceRepository,
)
from app.repositories.research_repo import (
    ResearchGapRepository, HypothesisRepository, ResearchNoteRepository,
)
from app.repositories.experiment_repo import (
    DatasetRepository, ExperimentRepository, ExperimentRunRepository, MetricRepository,
)
from app.repositories.report_repo import ReportRepository, CitationRepository
from app.repositories.job_repo import JobRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProjectRepository", "ResearchQuestionRepository",
    "PaperRepository", "PaperChunkRepository", "PaperSectionRepository", "PaperAuthorRepository",
    "EntityRepository", "RelationshipRepository", "ClaimRepository", "ClaimEvidenceRepository",
    "ResearchGapRepository", "HypothesisRepository", "ResearchNoteRepository",
    "DatasetRepository", "ExperimentRepository", "ExperimentRunRepository", "MetricRepository",
    "ReportRepository", "CitationRepository",
    "JobRepository",
]
