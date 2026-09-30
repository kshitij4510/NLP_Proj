"""
Domain exception hierarchy for ResearchMind.
All application-level errors derive from ResearchMindError.
"""
from __future__ import annotations

from typing import Any, Optional


class ResearchMindError(Exception):
    """Base exception for all ResearchMind errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


# ── Authentication / Authorization ────────────

class AuthenticationError(ResearchMindError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"


class AuthorizationError(ResearchMindError):
    status_code = 403
    error_code = "FORBIDDEN"


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"


# ── Resource errors ───────────────────────────

class NotFoundError(ResearchMindError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(ResearchMindError):
    status_code = 409
    error_code = "CONFLICT"


class ValidationError(ResearchMindError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


# ── Research domain errors ────────────────────

class ProjectError(ResearchMindError):
    error_code = "PROJECT_ERROR"


class PaperError(ResearchMindError):
    error_code = "PAPER_ERROR"


class IngestionError(ResearchMindError):
    error_code = "INGESTION_ERROR"


class RetrievalError(ResearchMindError):
    error_code = "RETRIEVAL_ERROR"


class EvidenceError(ResearchMindError):
    error_code = "EVIDENCE_ERROR"


class WorkflowError(ResearchMindError):
    error_code = "WORKFLOW_ERROR"


class ExperimentError(ResearchMindError):
    error_code = "EXPERIMENT_ERROR"


class VerificationError(ResearchMindError):
    error_code = "VERIFICATION_ERROR"


class ReportError(ResearchMindError):
    error_code = "REPORT_ERROR"


# ── External service errors ───────────────────

class ExternalAPIError(ResearchMindError):
    status_code = 502
    error_code = "EXTERNAL_API_ERROR"


class LLMError(ResearchMindError):
    status_code = 502
    error_code = "LLM_ERROR"


# ── File / storage errors ─────────────────────

class FileUploadError(ResearchMindError):
    status_code = 400
    error_code = "FILE_UPLOAD_ERROR"


class FileSizeError(FileUploadError):
    error_code = "FILE_TOO_LARGE"


class FileTypeError(FileUploadError):
    error_code = "INVALID_FILE_TYPE"


class PathTraversalError(ResearchMindError):
    status_code = 400
    error_code = "PATH_TRAVERSAL_DETECTED"


# ── Job errors ────────────────────────────────

class JobError(ResearchMindError):
    error_code = "JOB_ERROR"


class JobTimeoutError(JobError):
    error_code = "JOB_TIMEOUT"


class JobMaxRetriesError(JobError):
    error_code = "JOB_MAX_RETRIES"
