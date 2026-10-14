import io, zipfile
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.manuscripts import project_text, review_source
from app.services.citation_service import CitationService

def test_archive_excludes_secrets_and_dependencies():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        z.writestr("project/README.md","Useful project documentation")
        z.writestr("project/.env","SECRET_TOKEN=hidden")
        z.writestr("project/node_modules/test.js","irrelevant")
    text=project_text(stream.getvalue(),"project.zip")
    assert "Useful" in text and "SECRET_TOKEN" not in text and "irrelevant" not in text

def test_source_review_separates_evidence_from_proposal():
    gaps=review_source("However, our approach fails on multilingual retrieval benchmarks. We evaluate precision on the test set.")
    assert gaps[0]["evidence"].startswith("However")
    assert "controlled evaluation" in gaps[0]["change"]
    assert not any(g["kind"]=="Evaluation not documented" for g in gaps)

def test_bibtex_uses_conference_type_and_escapes():
    result=CitationService.format_bibtex({"title":"RAG & 50% improvement","authors":["A Person"],"venue":"Proceedings of ACL","year":2024})
    assert result.startswith("@inproceedings") and "booktitle" in result and r"\&" in result and r"\%" in result

def test_bad_archive_is_rejected():
    with pytest.raises(HTTPException): project_text(b"invalid","bad.zip")

def test_repository_review_does_not_treat_training_data_as_documentation():
    source="FILE: repo/README.md\nA tokenizer for research. Evaluation is performed using precision.\n\nFILE: repo/tests/story.txt\nHowever, the singer failed to perform at a musical festival in the winter."
    gaps=review_source(source)
    assert not any("singer" in g["evidence"] for g in gaps)
