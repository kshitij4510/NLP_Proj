"""Conservative source review with verbatim context, separate from research-gap discovery.

Keyword absence is a request for manual review, never evidence of a missing study.
"""
import re
import unicodedata
from pathlib import PurePosixPath


def normalize_passage(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()


def pdf_review_units(path: str) -> list[dict]:
    """Keep PDF paragraphs together and attach physical, one-based page numbers."""
    import fitz
    units = []
    with fitz.open(path) as document:
        for number, page in enumerate(document, 1):
            for block in page.get_text("blocks", sort=True):
                if len(block) >= 7 and block[6] == 0:
                    units.append({"text": block[4], "page": number})
    return units


def text_review_units(text: str) -> list[dict]:
    if "FILE: " in text:
        files = []
        for item in re.split(r"(?:^|\n\n)FILE: ", text)[1:]:
            filename, _, content = item.partition("\n")
            path = PurePosixPath(filename)
            if path.suffix.lower() in {".md", ".rst", ".tex"} and not any(part.lower() in {"data", "datasets", "fixtures", "tests"} for part in path.parts):
                files.append((filename, content))
        if files:
            return [{"text": paragraph, "source_file": filename} for filename, content in files for paragraph in re.split(r"\n\s*\n", content) if paragraph.strip()]
    return [{"text": paragraph} for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]


def _sentences(text: str) -> list[str]:
    # Do not split at PDF line wraps. Keep common scientific abbreviations together.
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]


def _proposal(kind: str, evidence: str) -> str:
    if kind == "author-stated future work":
        if re.search(r"jointly\s+pre.?train", evidence, re.I):
            return "To investigate this author-proposed direction, compare joint pre-training with the existing separately trained components under matched data and compute budgets. Report measured quality, cost, and ablations."
        if re.search(r"settings|translation|semantic parsing", evidence, re.I):
            return "Evaluate the application settings proposed by the authors using task-specific datasets and metrics, and compare with the relevant retrieve-and-edit baselines. Treat this as a proposed extension, not a missing experiment established by this review."
        return "Treat this as an existing author-proposed direction. Specify the task and comparison suggested in the passage, then define baselines and an evaluation protocol before claiming an improvement."
    if re.search(r"multilingual|cross.lingual", evidence, re.I):
        return "Add a controlled evaluation on held-out multilingual queries, with per-language results, a named baseline, uncertainty estimates, and failure examples."
    if re.search(r"contradict", evidence, re.I):
        return "Evaluate the documented conflict-handling limitation on passages with contradictory evidence; report how conflicts are detected and resolved against a baseline."
    if re.search(r"latency|comput|memory|cost", evidence, re.I):
        return "Evaluate the documented resource limitation with quality, latency, and memory measurements under matched hardware and workload conditions."
    if re.search(r"beam search|decod", evidence, re.I):
        return "Inspect the decoding procedure described alongside this constraint before proposing changes. If testing alternatives, compare decoding quality and inference cost under identical search budgets."
    return "Design a controlled evaluation of the specific limitation quoted here, with a named baseline, held-out data, uncertainty estimates, and observed failure cases."


def review_source_details(text: str, units: list[dict] | None = None) -> dict:
    units = text_review_units(text) if units is None else units
    passages = [{**unit, "text": normalize_passage(unit["text"])} for unit in units]
    findings = []
    seen = set()
    for unit in passages:
        sentences = _sentences(unit["text"])
        for index, sentence in enumerate(sentences):
            if not 35 <= len(sentence) <= 1800 or not re.search(r"[.!?][\"')\]]?$", sentence):
                continue  # Do not present cut-off text as a complete finding.
            future = bool(re.search(r"\bfuture work\b|\bfuture research\b", sentence, re.I))
            # "However" alone is a discourse marker, not a method limitation.
            own_limitation = bool(re.search(
                r"\b(?:our|this|the current|the)\s+(?:\w+[ -]){0,4}(?:approach|method|model|system|design|implementation|study|work)\b.{0,160}?\b(?:fails?|lacks?|limited|limitations?|cannot|unable|does not (?:support|address|evaluate)|do not (?:support|address|evaluate))\b"
                r"|\bwe\s+(?:cannot|are unable|do not (?:evaluate|address|support|consider))\b", sentence, re.I))
            if re.search(r"\b(?:previous|prior|earlier|existing)\s+(?:\w+\s+){0,3}(?:methods?|models?|systems?|work)\b", sentence, re.I):
                own_limitation = False
            if re.search(r"\b(?:not|never)\s+(?:fail\w*|limited)|\bno\s+(?:known\s+)?limitations?\b", sentence, re.I):
                own_limitation = False
            if not (future or own_limitation):
                continue
            evidence = sentence
            # Keep antecedents when a proposal refers to "these settings" or "this".
            if index and re.search(r"\b(?:these|those|this|such)\s+(?:settings|tasks|directions|approach|issue)|\b(?:this said|could represent)\b", sentence, re.I):
                evidence = " ".join(sentences[max(0, index - 2):index + 1])
            if evidence.casefold() in seen:
                continue
            seen.add(evidence.casefold())
            kind = "author-stated future work" if future else "source limitation"
            findings.append({"kind": kind, "evidence": evidence, "change": _proposal(kind, evidence),
                             "page": unit.get("page"), "source_file": unit.get("source_file"),
                             "basis": "Explicit source statement; interpretation requires author review."})
    checks = []
    for topic, pattern in [
        ("Evaluation", r"\b(?:evaluat\w*|benchmarks?|accuracy|precision|recall|f1|test set)\b"),
        ("Reproducibility", r"\b(?:seeds?|requirements|environment|installation|reproducib\w*|hyperparameters?|implementation details|training details|open[ -]?sourc\w*)\b|\bcode\b.{0,70}\b(?:available|released|https?)\b|github\.com/"),
        ("Ablation", r"\b(?:ablat\w*|component removal|without (?:the )?(?:retriever|generator|component))\b"),
    ]:
        located = next(((unit, match) for unit in passages if (match := re.search(pattern, unit["text"], re.I))), None)
        unit, match = located if located else ({}, None)
        excerpt = ""
        if match:
            excerpt = next((s for s in _sentences(unit["text"]) if re.search(pattern, s, re.I)), unit["text"])
        checks.append({"topic": topic, "status": "mention located" if located else "manual review needed",
                       "evidence": excerpt or "No matching passage was located by this text check. This does not establish that documentation or experiments are absent.",
                       "page": unit.get("page"), "source_file": unit.get("source_file"),
                       "note": "A matching mention is not a completeness or quality assessment. Inspect the paper and any linked code or supplementary material."})
    # Rank explicit limitations before future work, without treating missing keywords as gaps.
    findings.sort(key=lambda finding: finding["kind"] != "source limitation")
    return {"findings": findings[:8], "checks": checks}


def review_source(text: str) -> list[dict]:
    return review_source_details(text)["findings"]
