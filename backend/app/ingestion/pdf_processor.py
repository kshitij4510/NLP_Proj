"""
PDF processing — safe extraction of text and structure from PDFs.
Security: path traversal protection, file-size limits, no arbitrary code execution.
"""
from __future__ import annotations

import os
import pathlib
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import FileTypeError, FileSizeError, PathTraversalError
from app.core.logging import get_logger

logger = get_logger(__name__)

_ALLOWED_MIME = {"application/pdf"}
_MAX_BYTES = settings.max_upload_bytes


@dataclass
class PDFSection:
    title: Optional[str]
    content: str
    section_type: Optional[str]
    page_start: int
    page_end: int


@dataclass
class PDFDocument:
    title: Optional[str]
    abstract: Optional[str]
    sections: List[PDFSection] = field(default_factory=list)
    page_count: int = 0
    metadata: dict = field(default_factory=dict)


def _validate_pdf_path(path: str) -> pathlib.Path:
    """
    Validate the PDF path against path traversal attacks.
    Only allows paths within the configured upload directory.
    """
    upload_root = pathlib.Path(settings.UPLOAD_DIR).resolve()
    target = pathlib.Path(path).resolve()

    if not str(target).startswith(str(upload_root)):
        raise PathTraversalError(f"Path traversal detected: {path}")

    if not target.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    size = target.stat().st_size
    if size > _MAX_BYTES:
        raise FileSizeError(
            f"PDF exceeds max size ({size} > {_MAX_BYTES} bytes)"
        )

    return target


def extract_pdf(local_path: str) -> PDFDocument:
    """
    Extract text and structure from a PDF file.
    Uses PyMuPDF (fitz) as primary, pdfplumber as fallback.
    Never executes extracted content.
    """
    pdf_path = _validate_pdf_path(local_path)

    try:
        return _extract_with_pymupdf(str(pdf_path))
    except Exception as exc:
        logger.warning("pdf.pymupdf_failed", path=local_path, error=str(exc))
        try:
            return _extract_with_pdfplumber(str(pdf_path))
        except Exception as exc2:
            logger.error("pdf.extraction_failed", path=local_path, error=str(exc2))
            raise


def _extract_with_pymupdf(path: str) -> PDFDocument:
    import fitz  # PyMuPDF

    doc = fitz.open(path)
    sections: List[PDFSection] = []
    title: Optional[str] = doc.metadata.get("title")
    abstract: Optional[str] = None

    section_buffer: List[str] = []
    current_section_title: Optional[str] = None
    current_page_start = 0

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for block in blocks:
            if len(block) < 5:
                continue
            text = block[4].strip()
            if not text:
                continue

            # Heuristic: short all-caps or numbered lines are section headers
            if _is_section_header(text, block):
                if section_buffer:
                    content = " ".join(section_buffer).strip()
                    if content:
                        stype = _classify_section(current_section_title)
                        sections.append(PDFSection(
                            title=current_section_title,
                            content=content,
                            section_type=stype,
                            page_start=current_page_start,
                            page_end=page_num,
                        ))
                        if stype == "abstract" and abstract is None:
                            abstract = content[:2000]
                section_buffer = []
                current_section_title = text
                current_page_start = page_num
            else:
                section_buffer.append(text)

    # Final section
    if section_buffer:
        content = " ".join(section_buffer).strip()
        if content:
            sections.append(PDFSection(
                title=current_section_title,
                content=content,
                section_type=_classify_section(current_section_title),
                page_start=current_page_start,
                page_end=len(doc) - 1,
            ))

    doc.close()

    # Extract title from first section if not in metadata
    if not title and sections:
        title = sections[0].title or sections[0].content[:120]

    return PDFDocument(
        title=title,
        abstract=abstract,
        sections=sections,
        page_count=len(doc) if hasattr(doc, '__len__') else 0,
        metadata={"source": "pymupdf"},
    )


def _extract_with_pdfplumber(path: str) -> PDFDocument:
    import pdfplumber

    sections: List[PDFSection] = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                sections.append(PDFSection(
                    title=f"Page {page_num + 1}",
                    content=text.strip(),
                    section_type="body",
                    page_start=page_num,
                    page_end=page_num,
                ))

    return PDFDocument(
        title=None,
        abstract=None,
        sections=sections,
        page_count=len(sections),
        metadata={"source": "pdfplumber"},
    )


def _is_section_header(text: str, block: tuple) -> bool:
    """Heuristic: short text at large font size is likely a header."""
    if len(text) > 150:
        return False
    if len(text.split()) <= 1:
        return False
    # block[3] = y1 coordinate; bold/large font is harder to detect without font info
    # Use simple heuristics
    if text.isupper() and 3 <= len(text.split()) <= 8:
        return True
    if any(text.startswith(f"{i}.") or text.startswith(f"{i} ") for i in range(1, 20)):
        return True
    return False


def _classify_section(title: Optional[str]) -> str:
    if not title:
        return "body"
    t = title.lower()
    if any(k in t for k in ("abstract",)):
        return "abstract"
    if any(k in t for k in ("introduction",)):
        return "introduction"
    if any(k in t for k in ("related", "background", "literature")):
        return "related_work"
    if any(k in t for k in ("method", "approach", "model", "architecture")):
        return "methodology"
    if any(k in t for k in ("experiment", "evaluation", "result", "performance")):
        return "experiments"
    if any(k in t for k in ("conclusion", "discussion", "future")):
        return "conclusion"
    if any(k in t for k in ("reference", "bibliography")):
        return "references"
    return "body"
