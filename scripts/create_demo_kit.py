"""Create offline, synthetic inputs for the ResearchMind demonstration."""
from pathlib import Path
import zipfile
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
sections = [
    ("Abstract", "This synthetic demonstration paper describes VeriRAG, a retrieval and citation checking design for scientific question answering. It is a fictional teaching example, not published research. No experiments were executed and no measured improvements are claimed."),
    ("1. Introduction", "Retrieval augmented generation retrieves document passages before producing an answer. A citation can point to a relevant document while still failing to support the specific generated claim. We propose checking each answer claim against the retrieved passage and retaining its document and page provenance."),
    ("2. Method", "The proposed system splits searchable papers into passages, ranks passages with BM25, decomposes an answer into individual claims, and checks whether a supporting passage exists. Unsupported statements are flagged for human review. The implementation should preserve the original passage alongside each citation."),
    ("3. Proposed Evaluation", "Use a held-out test set of scientific questions with manually annotated supporting passages. Compare BM25 retrieval with a dense retrieval baseline under identical passage budgets. Record precision, recall, citation support rate, and latency. These are proposed metrics; this paper contains no measured results."),
    ("4. Limitations", "However, the method fails on multilingual queries because only English tokenization is specified. The current design lacks a procedure for resolving contradictory evidence across papers. Citation checks may fail when the supporting evidence spans several passages. Future work should evaluate robustness to noisy PDF extraction and missing page metadata."),
    ("5. Conclusion", "Claim-level citation review can make evidence inspection easier. This source intentionally omits component comparison experiments and environment setup instructions so reviewers can demonstrate documentation gap detection. All proposed changes require implementation and empirical validation."),
]
styles = getSampleStyleSheet()
styles["Title"].textColor = colors.HexColor("#30594f")
story = [Paragraph("VeriRAG: A Synthetic Citation Review Study", styles["Title"]),
         Paragraph("DEMONSTRATION ONLY | Fictional authors: Maya Iyer, Daniel Moss, Linh Tran", styles["Normal"]), Spacer(1, 16)]
for heading, body in sections:
    story.extend([Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 8)])
def footer(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.drawString(42, 28, "ResearchMind demo input - synthetic, not a published paper")
    canvas.drawRightString(550, 28, str(doc.page))
SimpleDocTemplate(str(OUT / "verirag_demo_paper.pdf"), title="VeriRAG Synthetic Citation Review Study", rightMargin=42, leftMargin=42, topMargin=38, bottomMargin=42).build(story, onFirstPage=footer, onLaterPages=footer)
markdown = "# VeriRAG demonstration project\n\n" + "\n\n".join("## " + h + "\n" + b for h, b in sections)
(OUT / "verirag_demo_project.md").write_text(markdown, encoding="utf-8")
with zipfile.ZipFile(OUT / "verirag_demo_project.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("verirag/README.md", markdown)
    archive.writestr("verirag/retriever.py", '"""Illustrative token matching; not an evaluated research system."""\ndef retrieve(query, passages):\n    tokens = set(query.lower().split())\n    return sorted(passages, key=lambda text: len(tokens & set(text.lower().split())), reverse=True)\n')
print(OUT)
