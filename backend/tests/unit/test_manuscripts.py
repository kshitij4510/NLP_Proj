import io, zipfile
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.manuscripts import project_text, review_source
from app.services.citation_service import CitationService
from app.services.source_review import review_source_details

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


def test_pdf_line_wraps_are_joined_and_page_is_preserved():
    result = review_source_details("", [{"text": "Our approach fails on multi-\nlingual retrieval\nqueries in unseen domains.", "page": 4}])
    finding = result["findings"][0]
    assert finding["evidence"] == "Our approach fails on multilingual retrieval queries in unseen domains."
    assert finding["page"] == 4
    assert "per-language" in finding["change"]


def test_background_however_is_not_a_proposed_method_limitation():
    assert review_source("However, their ability to access and precisely manipulate knowledge is still limited.") == []
    assert review_source("However, previous language models fail on multilingual retrieval benchmarks.") == []


def test_plural_ablations_and_code_release_are_located():
    result = review_source_details("", [
        {"text": "Retrieval Ablations\nWe freeze the retriever during training and compare alternatives.", "page": 7},
        {"text": "Code to run the experiments has been open-sourced on GitHub.", "page": 2},
    ])
    checks = {check["topic"]: check for check in result["checks"]}
    assert checks["Ablation"]["status"] == "mention located"
    assert checks["Ablation"]["page"] == 7
    assert checks["Reproducibility"]["status"] == "mention located"
    assert checks["Reproducibility"]["page"] == 2


def test_missing_keywords_request_review_without_asserting_absence():
    result = review_source_details("A simple scientific text describing passage ranking and document matching.")
    assert result["findings"] == []
    assert all(check["status"] == "manual review needed" for check in result["checks"])
    assert all("does not establish" in check["evidence"] for check in result["checks"])


def test_future_work_is_complete_contextual_and_labelled_as_existing():
    source = "Our approach also targets translation and parsing. These settings require additional study. This said, extending retrieval to these settings could represent promising future work."
    finding = review_source(source)[0]
    assert finding["kind"] == "author-stated future work"
    assert "translation and parsing" in finding["evidence"]
    assert finding["evidence"].endswith("future work.")
    assert "proposed extension" in finding["change"]


def test_incomplete_and_negated_limitation_is_not_reported():
    assert review_source("In future work, it may be fruitful to investigate if the two components") == []
    assert review_source("Our model does not fail on the multilingual retrieval test cases we evaluated.") == []


def test_scientific_ligatures_are_normalized_before_checks():
    checks = review_source_details("Reproducibility details include the conﬁguration and random seeds.")["checks"]
    assert next(c for c in checks if c["topic"] == "Reproducibility")["status"] == "mention located"
