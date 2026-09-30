"""
PDF downloader — safely fetches PDFs from URLs.
SSRF protection: validates hosts against allowlist.
File-size and MIME-type enforcement.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import urllib.parse
import uuid

import aiohttp

from app.core.config import settings
from app.core.exceptions import ExternalAPIError, FileSizeError, FileTypeError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allowed download hosts — extend as needed
_ALLOWED_DOWNLOAD_HOSTS = {
    "arxiv.org",
    "export.arxiv.org",
    "openreview.net",
    "proceedings.neurips.cc",
    "proceedings.mlr.press",
    "aclanthology.org",
    "www.aclanthology.org",
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "link.springer.com",
    "www.semanticscholar.org",
    "pdfs.semanticscholar.org",
}

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "binary/octet-stream",
}

_TIMEOUT = aiohttp.ClientTimeout(total=120, connect=10)


def _assert_allowed_download_host(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname not in _ALLOWED_DOWNLOAD_HOSTS:
        raise ExternalAPIError(
            f"SSRF protection: download host {parsed.hostname} not in allowlist"
        )


async def download_pdf(url: str, paper_id: uuid.UUID) -> str:
    """
    Download a PDF to the configured upload directory.
    Returns the local file path.
    Security: SSRF protection + MIME check + size limit.
    """
    _assert_allowed_download_host(url)

    upload_dir = pathlib.Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate a safe filename
    filename = f"{paper_id}.pdf"
    dest_path = upload_dir / filename

    # Path traversal check
    resolved = dest_path.resolve()
    if not str(resolved).startswith(str(upload_dir.resolve())):
        raise ExternalAPIError("Path traversal detected in download destination")

    headers = {
        "User-Agent": "ResearchMind/1.0 (academic research tool; mailto:research@example.com)"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=_TIMEOUT, allow_redirects=True) as resp:
            if resp.status != 200:
                raise ExternalAPIError(f"PDF download failed: {resp.status} {url}")

            # Content-type check
            ct = resp.content_type or ""
            if not any(allowed in ct for allowed in _ALLOWED_CONTENT_TYPES):
                # Some servers return text/html for PDFs — check content
                pass  # We'll validate by magic bytes after download

            # Stream to disk with size limit
            downloaded = 0
            hasher = hashlib.sha256()

            with open(dest_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    downloaded += len(chunk)
                    if downloaded > settings.max_upload_bytes:
                        dest_path.unlink(missing_ok=True)
                        raise FileSizeError(
                            f"PDF exceeds max size ({settings.MAX_UPLOAD_SIZE_MB}MB): {url}"
                        )
                    f.write(chunk)
                    hasher.update(chunk)

    # Validate magic bytes (PDF starts with %PDF)
    with open(dest_path, "rb") as f:
        magic = f.read(4)
    if magic != b"%PDF":
        dest_path.unlink(missing_ok=True)
        raise FileTypeError(f"Downloaded file is not a valid PDF: {url}")

    logger.info(
        "pdf.downloaded",
        paper_id=str(paper_id),
        size_bytes=downloaded,
        sha256=hasher.hexdigest()[:16],
    )
    return str(dest_path)
