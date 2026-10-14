from types import SimpleNamespace
from app.models.report import CitationStyle, ReportStatus
from app.services.ieee_export import render_ieee, escape_tex


def test_ieee_escapes_and_maps_citations():
    citation = SimpleNamespace(paper_id="p", style=CitationStyle.IEEE,
        in_text_citation="[1]", formatted_citation="Author, A & B, 2024.", metadata_snapshot={})
    report = SimpleNamespace(title="RAG & NLP_100%", abstract="Evidence [1]. Unknown [99].",
        citations=[citation, citation], status=ReportStatus.DRAFT, unsupported_claim_count=2,
        results="No measurements recorded.")
    source = render_ieee(report)
    assert r"\documentclass[conference]{IEEEtran}" in source
    assert r"RAG \& NLP\_100\%" in source
    assert r"\cite{ref1}" in source
    assert "[unresolved citation]" in source
    assert source.count(r"\bibitem{ref1}") == 1
    assert "Unsupported stored claims: 2" in source
    assert r"\end{document}" in source


def test_tex_commands_are_escaped():
    assert escape_tex(r"\input{secret}") == r"\textbackslash{}input\{secret\}"
