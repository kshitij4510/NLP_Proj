"""Report generation and retrieval endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, status, HTTPException

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
    await require_project(project_id, user, db)
    svc = ReportService(db)
    return await svc.generate(req)


from fastapi.responses import PlainTextResponse

@router.get("", response_model=PaginatedResponse[ReportRead])
async def list_reports(project_id: uuid.UUID, user: CurrentUser, db: DB):
    await require_project(project_id, user, db)
    svc = ReportService(db)
    items, total = await svc.list(project_id)
    return PaginatedResponse(items=items, total=total, page=1, page_size=20, pages=1)


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB):
    await require_project(project_id, user, db)
    svc = ReportService(db)
    return await require_report(svc, project_id, report_id)


@router.get("/{report_id}/export/markdown", response_class=PlainTextResponse)
async def export_markdown(
    project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB
):
    """Export the report in academic Markdown format."""
    await require_project(project_id, user, db)
    svc = ReportService(db)
    await require_report(svc, project_id, report_id)
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
    await require_project(project_id, user, db)
    svc = ReportService(db)
    await require_report(svc, project_id, report_id)
    content = await svc.to_bibtex(report_id)
    return PlainTextResponse(
        content=content,
        media_type="application/x-bibtex",
        headers={"Content-Disposition": f"attachment; filename=citations_{report_id}.bib"},
    )


async def require_project(project_id, user, db):
    from app.repositories.project_repo import ProjectRepository
    project = await ProjectRepository(db).get(project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(404, "Project not found")


async def require_report(svc, project_id, report_id):
    report = await svc.get(report_id)
    if not report or report.project_id != project_id:
        raise HTTPException(404, "Report not found")
    return report


@router.get("/{report_id}/export/ieee", response_class=PlainTextResponse)
async def export_ieee(project_id: uuid.UUID, report_id: uuid.UUID, user: CurrentUser, db: DB):
    await require_project(project_id, user, db)
    svc = ReportService(db)
    await require_report(svc, project_id, report_id)
    return PlainTextResponse(await svc.to_ieee(report_id), media_type="application/x-tex",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}_ieee.tex"})
