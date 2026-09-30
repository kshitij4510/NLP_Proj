"""Unit tests for CitationService formatting — no DB required."""
import pytest
from app.services.citation_service import CitationService
from app.models.report import CitationStyle


class MockAuthor:
    def __init__(self, name: str):
        self.name = name


class MockPaper:
    def __init__(self):
        self.title = "Attention Is All You Need"
        self.authors = [
            MockAuthor("Ashish Vaswani"),
            MockAuthor("Noam Shazeer"),
            MockAuthor("Niki Parmar"),
        ]
        self.year = 2017
        self.venue = "Advances in Neural Information Processing Systems"
        self.doi = "10.48550/arXiv.1706.03762"
        self.arxiv_id = "1706.03762"


def test_apa_format():
    paper = MockPaper()
    result = CitationService._format(paper, CitationStyle.APA)
    assert "Vaswani" in result
    assert "2017" in result
    assert "Attention Is All You Need" in result
    assert "doi.org" in result or "10.48550" in result


def test_bibtex_format():
    paper = MockPaper()
    result = CitationService._format(paper, CitationStyle.BIBTEX)
    assert result.startswith("@article{")
    assert "title" in result
    assert "author" in result
    assert "year" in result
    assert "2017" in result


def test_ieee_format():
    paper = MockPaper()
    result = CitationService._format(paper, CitationStyle.IEEE)
    assert "Attention Is All You Need" in result
    assert "2017" in result


def test_in_text_apa():
    paper = MockPaper()
    result = CitationService._in_text(paper, CitationStyle.APA)
    assert "Vaswani" in result
    assert "2017" in result
    assert result.startswith("(")
    assert result.endswith(")")


def test_bibtex_key():
    key = CitationService._bibtex_key(["Ashish Vaswani"], 2017)
    assert key == "vaswani2017"
