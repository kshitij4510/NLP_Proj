"""Report generation and retrieval endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DB
from app.schemas.common import PaginatedResponse
from app.schemas.report import ReportGenerateRequest, ReportRead
from app.services.report_service import ReportService

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["reports"])


@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    project_id: uuid.UUID, req: ReportGenerateRequest, user: CurrentUser, db: DB
):
    """
    Generate a full research report.
    Claim verification runs before report is finalized.
    Citations are generated from stored metadata only — never from LLM.
    """
    req.project_id = project_id
    svc = ReportService(db)
    return await svc.generate(req)


from fastapi.responses import PlainTextResponse

@router.get("", response_model=PaginatedResponse[ReportRead])
async def list_reports(project_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ReportService(db)
    items, total = await svc.list(project_id)
    return PaginatedResponse(items=items, total=total, page=1, page_size=20, pages=1)


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = ReportService(db)
    return await svc.get(report_id)


@router.get("/{report_id}/export/markdown", response_class=PlainTextResponse)
async def export_markdown(
    project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Export the report in academic Markdown format."""
    svc = ReportService(db)
    content = await svc.to_markdown(report_id)
    return PlainTextResponse(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.md"},
    )


@router.get("/{report_id}/export/bibtex", response_class=PlainTextResponse)
async def export_bibtex(
    project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Export the report citations in BibTeX format."""
    svc = ReportService(db)
    content = await svc.to_bibtex(report_id)
    return PlainTextResponse(
        content=content,
        media_type="application/x-bibtex",
        headers={"Content-Disposition": f"attachment; filename=citations_{report_id}.bib"},
    )
