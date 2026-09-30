"""
Academic literature discovery via external APIs.
Supports: OpenAlex, Semantic Scholar, arXiv.
All results are normalized to PaperSearchResult schema before touching the DB.
SSRF protection: only allowed academic API hostnames.
"""
from __future__ import annotations

import asyncio
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import aiohttp

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.core.logging import get_logger
from app.schemas.paper import PaperSearchResult

logger = get_logger(__name__)

# ── SSRF protection — allowlist ───────────────────────────────────────────────
_ALLOWED_HOSTS = {
    "api.semanticscholar.org",
    "api.openalex.org",
    "export.arxiv.org",
    "arxiv.org",
}

_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=5)


def _assert_allowed_host(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ExternalAPIError(f"SSRF protection: host {parsed.hostname} not allowed")


async def _get(session: aiohttp.ClientSession, url: str, params: dict) -> Dict[str, Any]:
    _assert_allowed_host(url)
    try:
        async with session.get(url, params=params, timeout=_DEFAULT_TIMEOUT) as resp:
            if resp.status == 429:
                raise ExternalAPIError("Rate limited by external API")
            if resp.status != 200:
                raise ExternalAPIError(f"External API error: {resp.status} {url}")
            return await resp.json()
    except aiohttp.ClientError as exc:
        raise ExternalAPIError(f"HTTP error: {exc}") from exc


# ── Semantic Scholar ───────────────────────────────────────────────────────────

async def search_semantic_scholar(
    query: str, limit: int = 20
) -> List[PaperSearchResult]:
    headers: Dict[str, str] = {}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,venue,externalIds,citationCount,openAccessPdf",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            data = await _get(session, url, params)
        except ExternalAPIError as exc:
            logger.warning("semantic_scholar.error", error=str(exc))
            return []

    results: List[PaperSearchResult] = []
    for paper in data.get("data", []):
        doi = (paper.get("externalIds") or {}).get("DOI")
        arxiv_id = (paper.get("externalIds") or {}).get("ArXiv")
        pdf_url = None
        if paper.get("openAccessPdf"):
            pdf_url = paper["openAccessPdf"].get("url")

        results.append(PaperSearchResult(
            title=paper.get("title", ""),
            abstract=paper.get("abstract"),
            authors=[a.get("name", "") for a in paper.get("authors", [])],
            year=paper.get("year"),
            venue=paper.get("venue"),
            doi=doi,
            arxiv_id=arxiv_id,
            pdf_url=pdf_url,
            citation_count=paper.get("citationCount", 0),
            source="semantic_scholar",
            relevance_score=None,
            external_id=paper.get("paperId"),
        ))
    return results


# ── OpenAlex ──────────────────────────────────────────────────────────────────

async def search_openalex(query: str, limit: int = 20) -> List[PaperSearchResult]:
    url = "https://api.openalex.org/works"
    params: Dict[str, Any] = {
        "search": query,
        "per-page": limit,
        "select": "title,abstract_inverted_index,authorships,publication_year,primary_location,doi,cited_by_count,open_access,ids",
    }
    if settings.OPENALEX_EMAIL:
        params["mailto"] = settings.OPENALEX_EMAIL

    async with aiohttp.ClientSession() as session:
        try:
            data = await _get(session, url, params)
        except ExternalAPIError as exc:
            logger.warning("openalex.error", error=str(exc))
            return []

    results: List[PaperSearchResult] = []
    for work in data.get("results", []):
        doi = work.get("doi", "").replace("https://doi.org/", "") or None
        arxiv_id = None
        ids = work.get("ids", {})
        if ids.get("arxiv"):
            arxiv_id = ids["arxiv"].replace("https://arxiv.org/abs/", "")

        # Reconstruct abstract from inverted index
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index", {}))

        authors = [
            a.get("author", {}).get("display_name", "")
            for a in work.get("authorships", [])
        ]

        venue = None
        if work.get("primary_location"):
            source = work["primary_location"].get("source") or {}
            venue = source.get("display_name")

        pdf_url = None
        if work.get("open_access", {}).get("oa_url"):
            pdf_url = work["open_access"]["oa_url"]

        results.append(PaperSearchResult(
            title=work.get("title", ""),
            abstract=abstract,
            authors=authors,
            year=work.get("publication_year"),
            venue=venue,
            doi=doi,
            arxiv_id=arxiv_id,
            pdf_url=pdf_url,
            citation_count=work.get("cited_by_count", 0),
            source="openalex",
            relevance_score=None,
            external_id=work.get("id"),
        ))
    return results


# ── arXiv ─────────────────────────────────────────────────────────────────────

async def search_arxiv(query: str, limit: int = 20) -> List[PaperSearchResult]:
    import xml.etree.ElementTree as ET

    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    async with aiohttp.ClientSession() as session:
        try:
            _assert_allowed_host(url)
            async with session.get(url, params=params, timeout=_DEFAULT_TIMEOUT) as resp:
                if resp.status != 200:
                    logger.warning("arxiv.error", status=resp.status)
                    return []
                text = await resp.text()
        except Exception as exc:
            logger.warning("arxiv.request_failed", error=str(exc))
            return []

    try:
        root = ET.fromstring(text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results: List[PaperSearchResult] = []

        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", "", ns) or "").strip()
            abstract = (entry.findtext("atom:summary", "", ns) or "").strip()
            authors = [
                a.findtext("atom:name", "", ns) or ""
                for a in entry.findall("atom:author", ns)
            ]
            arxiv_url = entry.findtext("atom:id", "", ns) or ""
            arxiv_id = arxiv_url.split("/abs/")[-1].strip()

            published = entry.findtext("atom:published", "", ns) or ""
            year = int(published[:4]) if published else None

            pdf_url = None
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                    break

            results.append(PaperSearchResult(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue="arXiv",
                doi=None,
                arxiv_id=arxiv_id,
                pdf_url=pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
                citation_count=0,
                source="arxiv",
                relevance_score=None,
                external_id=arxiv_id,
            ))
    except ET.ParseError as exc:
        logger.warning("arxiv.parse_error", error=str(exc))
        return []

    return results


# ── Multi-source discovery ─────────────────────────────────────────────────────

async def discover_papers(
    query: str,
    limit_per_source: int = 15,
    sources: Optional[List[str]] = None,
) -> List[PaperSearchResult]:
    """
    Query all configured academic APIs concurrently.
    Deduplicates by DOI and arXiv ID.
    """
    if sources is None:
        sources = ["semantic_scholar", "openalex", "arxiv"]

    tasks = []
    if "semantic_scholar" in sources:
        tasks.append(search_semantic_scholar(query, limit_per_source))
    if "openalex" in sources:
        tasks.append(search_openalex(query, limit_per_source))
    if "arxiv" in sources:
        tasks.append(search_arxiv(query, limit_per_source))

    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: List[PaperSearchResult] = []
    for r in results_nested:
        if isinstance(r, list):
            all_results.extend(r)
        elif isinstance(r, Exception):
            logger.warning("discovery.source_error", error=str(r))

    # Deduplicate by DOI or arXiv ID
    seen_dois: set = set()
    seen_arxiv: set = set()
    unique: List[PaperSearchResult] = []
    for paper in all_results:
        if paper.doi and paper.doi in seen_dois:
            continue
        if paper.arxiv_id and paper.arxiv_id in seen_arxiv:
            continue
        if paper.doi:
            seen_dois.add(paper.doi)
        if paper.arxiv_id:
            seen_arxiv.add(paper.arxiv_id)
        unique.append(paper)

    logger.info(
        "discovery.complete",
        query=query[:80],
        total=len(all_results),
        unique=len(unique),
    )
    return unique


# ── Utilities ─────────────────────────────────────────────────────────────────

def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> Optional[str]:
    """Reconstruct OpenAlex abstract from inverted index."""
    if not inverted_index:
        return None
    words: Dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    if not words:
        return None
    return " ".join(words[i] for i in sorted(words.keys()))
