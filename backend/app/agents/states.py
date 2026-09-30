"""
Workflow state machine definitions.
Implements the linear pipeline from spec §3 Agent/Workflow Layer:

PLANNING → DISCOVERY → INGESTION → ANALYSIS → EXTRACTION →
SYNTHESIS → GAP_ANALYSIS → HYPOTHESIS → EXPERIMENT_DESIGN →
VERIFICATION → REPORTING → COMPLETED

Every state transition is explicit, typed, logged, and persisted.
No uncontrolled recursion; each stage runs once per job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models.job import JobStage, JobStatus


# ── State input/output contracts ──────────────────────────────────────────────

@dataclass
class PlanningInput:
    project_id: str
    query: str
    keywords: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

@dataclass
class PlanningOutput:
    search_queries: list[str]
    sources: list[str]
    plan_summary: str

@dataclass
class DiscoveryInput:
    project_id: str
    search_queries: list[str]
    sources: list[str]
    limit_per_source: int = 15

@dataclass
class DiscoveryOutput:
    discovered: int
    added: int
    skipped: int

@dataclass
class IngestionInput:
    project_id: str
    batch_size: int = 5

@dataclass
class IngestionOutput:
    processed: int
    failed: int

@dataclass
class AnalysisInput:
    project_id: str

@dataclass
class AnalysisOutput:
    chunks_with_embeddings: int

@dataclass
class ExtractionInput:
    project_id: str

@dataclass
class ExtractionOutput:
    entities_extracted: int
    relations_extracted: int

@dataclass
class SynthesisInput:
    project_id: str

@dataclass
class SynthesisOutput:
    synthesis: dict
    evidence_count: int

@dataclass
class GapAnalysisInput:
    project_id: str
    synthesis: dict
    evidence_snippets: list[dict]

@dataclass
class GapAnalysisOutput:
    gaps_detected: int

@dataclass
class HypothesisInput:
    project_id: str
    gap_ids: list[str]

@dataclass
class HypothesisOutput:
    hypotheses_generated: int

@dataclass
class ExperimentDesignInput:
    project_id: str
    hypothesis_ids: list[str]

@dataclass
class ExperimentDesignOutput:
    experiments_designed: int

@dataclass
class VerificationInput:
    project_id: str

@dataclass
class VerificationOutput:
    verification_summary: dict
    unsupported_claims: int

@dataclass
class ReportingInput:
    project_id: str
    citation_styles: list[str] = field(default_factory=lambda: ["apa"])
    verify_claims: bool = True

@dataclass
class ReportingOutput:
    report_id: str
    unsupported_claims: int

@dataclass
class WorkflowContext:
    """Carries accumulated state across all pipeline stages."""
    project_id: str
    job_id: str
    current_stage: JobStage = JobStage.PLANNING
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stage_outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def record_stage_output(self, stage: JobStage, output: Any) -> None:
        self.stage_outputs[stage.value] = output
        self.current_stage = stage

    def fail(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        self.status = JobStatus.COMPLETED
        self.current_stage = JobStage.COMPLETED
        self.completed_at = datetime.now(timezone.utc)


# ── Transition table (spec §3 Agent/Workflow Layer) ───────────────────────────
STAGE_TRANSITIONS: Dict[JobStage, Optional[JobStage]] = {
    JobStage.PLANNING:          JobStage.DISCOVERY,
    JobStage.DISCOVERY:         JobStage.INGESTION,
    JobStage.INGESTION:         JobStage.ANALYSIS,
    JobStage.ANALYSIS:          JobStage.EXTRACTION,
    JobStage.EXTRACTION:        JobStage.SYNTHESIS,
    JobStage.SYNTHESIS:         JobStage.GAP_ANALYSIS,
    JobStage.GAP_ANALYSIS:      JobStage.HYPOTHESIS,
    JobStage.HYPOTHESIS:        JobStage.EXPERIMENT_DESIGN,
    JobStage.EXPERIMENT_DESIGN: JobStage.VERIFICATION,
    JobStage.VERIFICATION:      JobStage.REPORTING,
    JobStage.REPORTING:         JobStage.COMPLETED,
    JobStage.COMPLETED:         None,
}


def next_stage(current: JobStage) -> Optional[JobStage]:
    return STAGE_TRANSITIONS.get(current)
