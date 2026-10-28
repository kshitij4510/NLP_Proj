"""Render the implementation-grounded viva guide with ReportLab."""
import html
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/researchmind_viva_guide.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
for name, filename in [("Guide", "arial.ttf"), ("GuideBold", "arialbd.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))
pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="GuideBold", italic="Guide", boldItalic="GuideBold")
INK = colors.HexColor("#18372f")
MUTED = colors.HexColor("#5d6d69")
styles = {
    "body": ParagraphStyle("body", fontName="Guide", fontSize=10.2, leading=13.9, spaceAfter=7, textColor=colors.HexColor("#202b28")),
    "chapter": ParagraphStyle("chapter", fontName="GuideBold", fontSize=21, leading=26, spaceAfter=19, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="GuideBold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=7, keepWithNext=True, textColor=INK),
    "cover": ParagraphStyle("cover", fontName="GuideBold", fontSize=37, leading=44, textColor=INK, spaceAfter=18),
    "deck": ParagraphStyle("deck", fontName="Guide", fontSize=15, leading=22, textColor=MUTED, spaceAfter=18),
    "small": ParagraphStyle("small", fontName="Guide", fontSize=9.4, leading=14, textColor=MUTED, spaceAfter=7),
}

def text_markup(text):
    escaped = html.escape(text)
    return re.sub(r"(https?://[^\s]+)", lambda m: '<link href="'+m[1]+'" color="#236d5a">'+m[1]+'</link>', escaped)

def page_decor(canvas, doc):
    width, height = doc.pagesize
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#dce6e1"))
    if doc.page > 1:
        canvas.setFont("Guide", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(46, height-28, "RESEARCHMIND  /  PROJECT & VIVA GUIDE")
        canvas.line(46, height-36, width-46, height-36)
    canvas.line(46, 37, width-46, 37)
    canvas.setFont("Guide", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(46, 24, "Implementation-grounded preparation | Human review remains necessary")
    canvas.drawRightString(width-46, 24, str(doc.page))
    canvas.restoreState()

source = (ROOT / "docs/researchmind-viva-guide.md").read_text(encoding="utf-8")
chapters = re.findall(r"^## (.+)$", source, re.M)
story = [Spacer(1, 48), Paragraph("ResearchMind", styles["cover"]),
         Paragraph("Project &amp; Viva Guide", styles["deck"]),
         Paragraph("60 questions with answers. NLP concepts, formulas, implementation details, and a complete real-paper demonstration.", styles["deck"]),
         Spacer(1, 13), Paragraph("STUDY MAP", styles["sub"])]
for chapter in chapters:
    story.append(Paragraph(text_markup(chapter), styles["small"]))
story.extend([Spacer(1, 20), Paragraph("Read Sections 1-4 first. Practise the questions in Sections 5-8. Rehearse Section 9 with the original RAG paper. Use Sections 10-12 for troubleshooting, final revision, and references.", styles["body"]),
              Paragraph("This guide distinguishes code capabilities from the current local demo. It does not claim that example metrics or generated research proposals are measured scientific results.", styles["small"])])

body = source[source.index("## 1."):]
body = re.sub(r"^(### [^\n]+)\n(?!\n)", r"\1\n\n", body, flags=re.M)
body = re.sub(r"\n(?=\d+\. )", "\n\n", body)
for block in re.split(r"\n\s*\n", body):
    block = block.strip()
    if not block:
        continue
    if block.startswith("## "):
        story.extend([PageBreak(), Paragraph(text_markup(block[3:]), styles["chapter"])])
    elif block.startswith("### "):
        story.append(Paragraph(text_markup(block[4:]), styles["sub"]))
    else:
        story.append(Paragraph(text_markup(" ".join(block.splitlines())), styles["body"]))

SimpleDocTemplate(str(OUT), pagesize=(595.28, 841.89), rightMargin=46, leftMargin=46,
                  topMargin=53, bottomMargin=51, title="ResearchMind Project and Viva Guide",
                  author="ResearchMind project preparation").build(story, onFirstPage=page_decor, onLaterPages=page_decor)
print(OUT)
