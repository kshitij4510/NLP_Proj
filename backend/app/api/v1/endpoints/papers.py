"""Paper management and upload endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import Depends, APIRouter, Query, UploadFile, File, status

from app.api.deps import CurrentUser, DB, require_project_access
from app.core.config import settings
from app.core.exceptions import FileTypeError, FileSizeError
from app.models.paper import PaperStatus
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.paper import PaperCreate, PaperRead
from app.services.paper_service import PaperService

router = APIRouter(prefix="/projects/{project_id}/papers", tags=["papers"], dependencies=[Depends(require_project_access)])


@router.post("", response_model=PaperRead, status_code=status.HTTP_201_CREATED)
async def add_paper(project_id: uuid.UUID, data: PaperCreate, user: CurrentUser, db: DB):
    """Add a paper by DOI, arXiv ID, or PDF URL."""
    from app.repositories.paper_repo import PaperRepository
    svc = PaperService(db)
    paper = await svc.add_paper(project_id, user.id, data)
    # Eagerly reload with authors to avoid lazy-load outside session
    repo = PaperRepository(db)
    return await repo.get_with_authors(paper.id)


@router.post("/upload", response_model=PaperRead, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    file: UploadFile = File(...),
):
    """Upload a PDF file directly."""
    import pathlib
    import os

    # Security: validate extension and MIME type
    filename = file.filename or ""
    ext = pathlib.Path(filename).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise FileTypeError(f"Only {settings.ALLOWED_UPLOAD_EXTENSIONS} files are allowed")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise FileSizeError(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Validate PDF magic bytes
    if not content.startswith(b"%PDF"):
        raise FileTypeError("Uploaded file is not a valid PDF")

    # Save to upload directory
    paper_id = uuid.uuid4()
    upload_dir = pathlib.Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{paper_id}.pdf"

    with open(dest, "wb") as f:
        f.write(content)

    svc = PaperService(db)
    paper = await svc.add_paper(
        project_id,
        user.id,
        PaperCreate(title=pathlib.Path(filename).stem),
    )
    # Store local path
    from app.repositories.paper_repo import PaperRepository
    await PaperRepository(db).update(paper.id, local_pdf_path=str(dest))
    return await PaperRepository(db).get_with_authors(paper.id)


@router.get("", response_model=PaginatedResponse[PaperRead])
async def list_papers(
    project_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    status_filter: Optional[PaperStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    svc = PaperService(db)
    offset = (page - 1) * page_size
    items, total = await svc.list(
        project_id, user.id, status=status_filter, offset=offset, limit=page_size
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{paper_id}", response_model=PaperRead)
async def get_paper(project_id: uuid.UUID, paper_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = PaperService(db)
    return await svc.get(paper_id, user.id)


@router.delete("/{paper_id}", response_model=SuccessResponse)
async def delete_paper(project_id: uuid.UUID, paper_id: uuid.UUID, user: CurrentUser, db: DB):
    svc = PaperService(db)
    await svc.delete(paper_id, user.id)
    return SuccessResponse(message="Paper deleted")


from pydantic import BaseModel, Field
class DiscoveryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)

@router.post("/discover/search", response_model=dict)
async def discover(project_id: uuid.UUID, data: DiscoveryRequest, user: CurrentUser, db: DB):
    from app.services.project_service import ProjectService
    from app.ingestion.ingestion_pipeline import IngestionPipeline
    await ProjectService(db).get(project_id, user.id)
    result = await IngestionPipeline(db).run_discovery(project_id, data.query, 60)
    result["ingestion"] = await IngestionPipeline(db).run_ingestion(project_id, batch_size=200)
    return result
