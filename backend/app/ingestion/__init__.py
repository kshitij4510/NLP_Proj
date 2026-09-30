"""ResearchMind ingestion layer."""
from app.ingestion.academic_apis import discover_papers
from app.ingestion.downloader import download_pdf
from app.ingestion.pdf_processor import extract_pdf
from app.ingestion.ingestion_pipeline import IngestionPipeline

__all__ = ["discover_papers", "download_pdf", "extract_pdf", "IngestionPipeline"]
