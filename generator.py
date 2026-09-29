"""Formatting utilities: sanitize text and build .docx, .pdf and HTML preview output."""
import html
import io
import re
import unicodedata

from config import COMPANY_FOOTER, LOGO_PATH

# --------------------------------------------------------------------------- sanitize
_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2022": "-", "\u25cf": "-",
    "\u25aa": "-", "\u2026": "...", "\u00a0": " ", "\u2192": "->", "\u2264": "<=", "\u2265": ">=",
}


def sanitize_text(text: str) -> str:
    """Remove typographic quotes/special characters so every export format renders cleanly."""
    if not text:
        return ""
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # keep Latin-1 characters (accents, section sign, etc.), drop the rest
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if ch in "\n\t" or (ord(ch) >= 32 and ord(ch) <= 255))
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- parsing
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_HEAD_HASH = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^\s*(?:[-*]|\d+\)|[a-z]\))\s+(.*)$")
_BOLD_LINE = re.compile(r"^\*\*(.+?)\*\*:?$")
_NUM_HEAD = re.compile(r"^(?:\d+\.|ARTICLE\s+\w+|SECTION\s+\w+)[^.]{0,90}:$", re.I)
_CAPS_HEAD = re.compile(r"^[A-Z][A-Z0-9\s,&'/-]{3,80}:?$")


def _plain(s: str) -> str:
    return _BOLD.sub(r"\1", s).replace("**", "").replace("`", "").strip()


def parse_blocks(text: str, doc_type: str = ""):
    """Split raw AI text into ('heading'|'bullet'|'para', text) blocks."""
    blocks = []
    for raw in sanitize_text(text).split("\n"):
        line = raw.strip()
        if not line or set(line) <= set("-_=* "):
            continue
        m = _HEAD_HASH.match(line)
        if m:
            blocks.append(("heading", _plain(m.group(2))))
            continue
        m = _BOLD_LINE.match(line)
        if m:
            blocks.append(("heading", _plain(m.group(1)).rstrip(":") + ":"))
            continue
        if _NUM_HEAD.match(line) or _CAPS_HEAD.match(line):
            blocks.append(("heading", _plain(line)))
            continue
        m = _BULLET.match(line)
        if m and not line.startswith("**"):
            blocks.append(("bullet", m.group(1).strip()))
            continue
        blocks.append(("para", line))
    # the document title is printed separately, so drop a duplicate first heading
    if blocks and blocks[0][0] == "heading" and doc_type:
        first = blocks[0][1].lower().strip(" :")
        if first in doc_type.lower() or doc_type.lower() in first:
            blocks = blocks[1:]
    return blocks


def split_terms(terms: str):
    return [t.strip() for t in (terms or "").replace("\n", ";").split(";") if t.strip()]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "document").lower()).strip("_") or "document"


# --------------------------------------------------------------------------- HTML preview
def format_html_preview(text: str) -> str:
    """Convert output to stylized HTML blocks for inline display."""
    out, in_list = [], False
    for kind, content in parse_blocks(text):
        safe = html.escape(_plain(content) if kind == "heading" else content)
        safe = _BOLD.sub(r"<b>\1</b>", safe).replace("**", "")
        if kind != "bullet" and in_list:
            out.append("</ul>")
            in_list = False
        if kind == "heading":
            out.append(f"<h4 style='margin:18px 0 6px 0;color:#f5f5f5;'>{safe}</h4>")
        elif kind == "bullet":
            if not in_list:
                out.append("<ul style='margin:4px 0 8px 22px;'>")
                in_list = True
            out.append(f"<li>{safe}</li>")
        else:
            out.append(f"<p style='margin:6px 0;line-height:1.55;'>{safe}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# --------------------------------------------------------------------------- DOCX
def format_docx(text: str, doc_type: str, terms: str = "") -> bytes:
    """Word document: logo, Times New Roman, headings, optional Terms table, footer."""
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt

    doc_type = sanitize_text(doc_type) or "Legal Document"
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Inches(1)
        sec.top_margin = sec.bottom_margin = Inches(1)

    def add_runs(par, content):
        for i, piece in enumerate(_BOLD.split(content)):
            if piece:
                run = par.add_run(piece.replace("**", ""))
                run.bold = bool(i % 2)

    if LOGO_PATH.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(LOGO_PATH), width=Inches(2.0))

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc_type.upper())
    run.bold = True
    run.font.size = Pt(16)
    title.paragraph_format.space_after = Pt(14)

    for kind, content in parse_blocks(text, doc_type):
        if kind == "heading":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            r = p.add_run(content)
            r.bold = True
        elif kind == "bullet":
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, content)
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(6)
            add_runs(p, content)

    term_list = [sanitize_text(t) for t in split_terms(terms)]
    if term_list:
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.add_run("Schedule of Key Terms").bold = True
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text = "No.", "Term / Condition"
        for c in hdr:
            for r in c.paragraphs[0].runs:
                r.bold = True
        for i, t in enumerate(term_list, 1):
            row = table.add_row().cells
            row[0].text, row[1].text = str(i), t
        for row in table.rows:
            row.cells[0].width = Inches(0.6)
            row.cells[1].width = Inches(5.9)

    # footer with page number
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run(COMPANY_FOOTER + "  |  Page ")
    fr.italic = True
    fr.font.size = Pt(9)
    num = footer.add_run()
    num.font.size = Pt(9)
    for tag, attr in (("w:fldChar", "begin"), ("w:instrText", None), ("w:fldChar", "end")):
        el = OxmlElement(tag)
        if attr:
            el.set(qn("w:fldCharType"), attr)
        else:
            el.set(qn("xml:space"), "preserve")
            el.text = "PAGE"
        num._r.append(el)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- PDF
def format_pdf(text: str, doc_type: str, terms: str = "") -> bytes:
    """Branded PDF: logo header on every page, bold headings, bullet terms, footer."""
    from fpdf import FPDF

    doc_type = sanitize_text(doc_type) or "Legal Document"
    logo_w = 38.0
    logo_h = 0.0
    if LOGO_PATH.exists():
        from PIL import Image

        with Image.open(LOGO_PATH) as im:
            logo_h = logo_w * im.height / im.width

    class LegalPDF(FPDF):
        def header(self):
            y = 8
            if logo_h:
                self.image(str(LOGO_PATH), x=(self.w - logo_w) / 2, y=y, w=logo_w)
                y += logo_h + 2
            self.set_y(y)
            self.set_font("Helvetica", "B", 12)
            self.cell(0, 8, doc_type, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(160, 160, 160)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(5)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(90, 90, 90)
            self.cell(0, 8, f"{COMPANY_FOOTER}   Page {self.page_no()}/{{nb}}", align="C")
            self.set_text_color(0, 0, 0)

    pdf = LegalPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    def heading(txt):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 6, txt, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def para(txt):
        pdf.set_font("Helvetica", "", 10.5)
        pdf.multi_cell(0, 5.6, txt, align="J", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    def bullet(txt):
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_x(pdf.l_margin + 5)
        pdf.multi_cell(0, 5.6, "-  " + txt, new_x="LMARGIN", new_y="NEXT")

    for kind, content in parse_blocks(text, doc_type):
        content = _plain(content)
        {"heading": heading, "bullet": bullet, "para": para}[kind](content)

    term_list = [sanitize_text(t) for t in split_terms(terms)]
    if term_list:
        heading("Schedule of Key Terms")
        for t in term_list:
            bullet(t)

    return bytes(pdf.output())
