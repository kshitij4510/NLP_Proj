"""IEEE conference manuscript source from stored report artifacts."""
import re


def escape_tex(text):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(c, c) for c in str(text or ""))


def render_ieee(report):
    citations = {}
    for citation in report.citations:
        key = str(citation.paper_id)
        if key not in citations or citation.style.value == "ieee":
            citations[key] = citation
    refs = sorted(citations.values(), key=lambda c: int(c.in_text_citation[1:-1])
                  if c.in_text_citation and re.fullmatch(r"\[\d+\]", c.in_text_citation) else 1000000)

    def body(text, link_citations=True):
        text = str(text or "")
        text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
        urls = []
        def stash_url(match):
            urls.append(match.group(0))
            return "URLTOKEN" + str(len(urls)-1) + "ENDTOKEN"
        text = re.sub(r"https?://[^\s)<>]+", stash_url, text)
        escaped = escape_tex(text)
        for i, url in enumerate(urls):
            safe_url = url.replace("{", "%7B").replace("}", "%7D").replace("\\", "%5C")
            escaped = escaped.replace("URLTOKEN"+str(i)+"ENDTOKEN", r"\url{" + safe_url + "}")
        def cite(match):
            n = int(match.group(1))
            return r"\cite{ref" + str(n) + "}" if 1 <= n <= len(refs) else "[unresolved citation]"
        return re.sub(r"\[(\d+)\]", cite, escaped) if link_citations else escaped

    provenance = getattr(report, "verification_summary", None) or {}
    author = provenance.get("author") or "Author name"
    affiliation = provenance.get("affiliation") or "Affiliation"
    lines = [r"\documentclass[conference]{IEEEtran}", r"\usepackage[T1]{fontenc}",
             r"\usepackage[utf8]{inputenc}", r"\usepackage{cite}", r"\usepackage{xurl}",
             r"\begin{document}", r"\title{" + escape_tex(report.title) + "}",
             r"\author{\IEEEauthorblockN{" + escape_tex(author) + r"}\IEEEauthorblockA{" + escape_tex(affiliation) + "}}",
             r"\maketitle", r"\begin{abstract}", body(report.abstract), r"\end{abstract}"]
    sections = [("Introduction", "research_question_section"), ("Background and Related Work", "background"),
                ("Literature Review", "literature_review"), ("Research Landscape", "research_landscape"),
                ("System Design and Source Analysis", "method_comparison"), ("Potential Research Gaps", "research_gaps_section"),
                ("Proposed Hypotheses", "hypotheses_section"), ("Experimental Design", "experimental_design"),
                ("Results", "results"), ("Ablation Study", "ablation_study"), ("Limitations", "limitations"),
                ("Future Work", "future_work"), ("Conclusion", "conclusion")]
    for title, field in sections:
        content = getattr(report, field, None)
        if content:
            lines += [r"\section{" + title + "}", body(content, not (field == "method_comparison" and provenance.get("scope") == "source-specific revision"))]
    lines += [r"\section{Verification and Provenance}",
              escape_tex(f"Automatically generated research draft. Status: {report.status.value}. "
                         f"Unsupported stored claims: {report.unsupported_claim_count}. "
                         "Stored-claim verification does not independently validate generated prose. "
                         "Author review is required; missing experimental results are not measured outcomes.")]
    if refs:
        lines.append(r"\begin{thebibliography}{" + str(len(refs)) + "}")
        for i, citation in enumerate(refs, 1):
            meta = citation.metadata_snapshot or {}
            text = citation.formatted_citation
            if citation.style.value != "ieee":
                text = ", ".join(filter(None, [", ".join(meta.get("authors") or []),
                    meta.get("title"), meta.get("venue"), str(meta.get("year") or "n.d.")]))
            lines.append(r"\bibitem{ref" + str(i) + "} " + escape_tex(text))
        lines.append(r"\end{thebibliography}")
    lines.append(r"\end{document}")
    return "\n\n".join(lines) + "\n"
