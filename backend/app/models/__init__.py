"""
ResearchMind models — import all here so SQLAlchemy registers them.
"""
from app.models.base import Base
from app.models.user import User
from app.models.project import ResearchProject, ResearchQuestion, ProjectStatus
from app.models.paper import Paper, PaperAuthor, PaperSection, PaperChunk, PaperStatus
from app.models.knowledge import (
    Entity, Relationship, Claim, ClaimEvidence,
    EntityType, RelationType, VerificationStatus, ArtifactType,
)
from app.models.research import (
    ResearchGap, Hypothesis, ResearchNote,
    GapType, HypothesisStatus,
)
from app.models.experiment import (
    Experiment, ExperimentRun, Metric, Dataset, ExperimentStatus,
)
from app.models.report import Report, Citation, ReportStatus, CitationStyle
from app.models.job import ResearchJob, JobStage, JobStatus

__all__ = [
    "Base",
    "User",
    "ResearchProject", "ResearchQuestion", "ProjectStatus",
    "Paper", "PaperAuthor", "PaperSection", "PaperChunk", "PaperStatus",
    "Entity", "Relationship", "Claim", "ClaimEvidence",
    "EntityType", "RelationType", "VerificationStatus", "ArtifactType",
    "ResearchGap", "Hypothesis", "ResearchNote",
    "GapType", "HypothesisStatus",
    "Experiment", "ExperimentRun", "Metric", "Dataset", "ExperimentStatus",
    "Report", "Citation", "ReportStatus", "CitationStyle",
    "ResearchJob", "JobStage", "JobStatus",
]
