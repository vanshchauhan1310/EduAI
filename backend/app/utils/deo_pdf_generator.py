"""
DEO PDF and DOCX generation utility using ReportLab and python-docx.
Generates government-format DEO reports as PDF and DOCX bytes with sharing support.
"""
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
from xml.sax.saxutils import escape as xml_escape


# ─── Government colour palette ────────────────────────────────────
GOV_BLUE   = colors.HexColor("#1d4ed8")
GOV_DARK   = colors.HexColor("#1e3a8a")
GOV_GREEN  = colors.HexColor("#059669")
GOV_RED    = colors.HexColor("#dc2626")
LIGHT_GRAY = colors.HexColor("#f3f4f6")
MID_GRAY   = colors.HexColor("#6b7280")


# ─── Register Telugu-compatible fonts ────────────────────────────
def _register_fonts():
    """Register fonts that support Telugu and other Indic scripts."""
    search_dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/opentype",
        "/System/Library/Fonts",
        "C:\\Windows\\Fonts",
    ]
    name_tokens = ("telugu", "noto", "dejavu", "mry", "lohit")
    registered = set()
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                lf = f.lower()
                if not lf.endswith(".ttf"):
                    continue
                if not any(tok in lf for tok in name_tokens):
                    continue
                path = os.path.join(root, f)
                font_internal_name = os.path.splitext(f)[0]
                if font_internal_name in registered:
                    continue
                try:
                    pdfmetrics.registerFont(TTFont(font_internal_name, path))
                    registered.add(font_internal_name)
                except Exception:
                    continue
    explicit = [
        "/usr/share/fonts/opentype/noto/NotoSansTelugu-Regular.ttf",
        "C:\\Windows\\Fonts\\NotoSansTelugu-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\DejaVuSans.ttf",
    ]
    for path in explicit:
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            if name not in registered:
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    registered.add(name)
                except Exception:
                    pass

_register_fonts()


def _base_styles() -> dict:
    base = getSampleStyleSheet()
    registered = set(pdfmetrics.getRegisteredFontNames())
    preferred = [
        ("NotoSansTelugu", "NotoSansTelugu-Bold"),
        ("NotoSansTelugu-Regular", "NotoSansTelugu-Bold"),
        ("DejaVuSans", "DejaVuSans-Bold"),
        ("DejaVuSans", "DejaVuSans"),
        ("Helvetica", "Helvetica-Bold"),
    ]
    body_font = "Helvetica"
    body_bold_font = "Helvetica-Bold"
    for regular, bold in preferred:
        if regular in registered:
            body_font = regular
            body_bold_font = bold if bold in registered else regular
            break
    return {
        "header":      ParagraphStyle("header",      fontSize=14, fontName=body_bold_font, textColor=GOV_DARK,   alignment=TA_CENTER,  spaceAfter=4),
        "subheader":   ParagraphStyle("subheader",   fontSize=11, fontName=body_bold_font, textColor=GOV_BLUE,   alignment=TA_CENTER,  spaceAfter=2),
        "normal":      ParagraphStyle("normal",      fontSize=10, fontName=body_font,      leading=14,           spaceAfter=6,         alignment=TA_JUSTIFY),
        "small":       ParagraphStyle("small",       fontSize=8,  fontName=body_font,      textColor=MID_GRAY),
        "section":     ParagraphStyle("section",     fontSize=12, fontName=body_bold_font, textColor=GOV_DARK,   spaceAfter=4,         spaceBefore=14),
        "subsection":  ParagraphStyle("subsection",  fontSize=11, fontName=body_bold_font, textColor=GOV_BLUE,   spaceAfter=3,         spaceBefore=10),
        "bullet":      ParagraphStyle("bullet",      fontSize=10, fontName=body_font,      leading=14,           leftIndent=16,        spaceAfter=3),
        "urgent":      ParagraphStyle("urgent",      fontSize=10, fontName=body_bold_font, textColor=GOV_RED,    leading=14,           spaceAfter=6),
        "success":     ParagraphStyle("success",     fontSize=10, fontName=body_font,      textColor=GOV_GREEN,  leading=14,           spaceAfter=6),
    }


def _deo_letterhead(styles: dict) -> list:
    return [
        Paragraph("GOVERNMENT OF ANDHRA PRADESH", styles["header"]),
        Paragraph("Department of School Education", styles["subheader"]),
        Paragraph("District Education Officer - Governance Platform", styles["small"]),
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=2, color=GOV_BLUE),
        HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE),
        Spacer(1, 4 * mm),
    ]


def _confidential_footer(styles: dict) -> list:
    return [
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY),
        Spacer(1, 2 * mm),
        Paragraph(
            f"CONFIDENTIAL | EduAI DEO Copilot | {date.today().strftime('%d %B %Y')}",
            styles["small"],
        ),
    ]


# ─── DEO Report Type PDF Generation ───────────────────────────────

def generate_deo_report_pdf(content: str, report_type: str, title: str | None = None, reference: str | None = None) -> bytes:
    """Render a DEO report as a government-formatted A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    )
    styles = _base_styles()
    elements: list = []

    elements.extend(_deo_letterhead(styles))

    # Report title
    report_title = title or report_type.replace("_", " ").upper()
    elements.append(Paragraph(f"<b>{report_title}</b>", styles["header"]))
    elements.append(Spacer(1, 2 * mm))

    if reference:
        elements.append(Paragraph(f"<b>Ref. No.:</b> {reference}", styles["small"]))
        elements.append(Paragraph(f"<b>Date:</b> {date.today().strftime('%d-%m-%Y')}", styles["small"]))
        elements.append(Spacer(1, 4 * mm))

    # Parse content and render with appropriate styles
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 3 * mm))
            continue

        # Escape XML special characters for ReportLab Paragraph
        safe = xml_escape(stripped)

        # Detect section headings
        upper_words = [w for w in safe.split() if w.isupper() and len(w) > 2]
        is_heading = (len(upper_words) >= 3) or safe.endswith(":") or safe.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))

        if is_heading:
            elements.append(Paragraph(f"<b>{safe}</b>", styles["subsection"]))
        elif safe.startswith(("•", "-", "*", "➢", "→")):
            elements.append(Paragraph(f"• {safe.lstrip('•-*➢→ ')}", styles["bullet"]))
        elif safe.startswith(("URGENT", "IMMEDIATE", "CRITICAL")):
            elements.append(Paragraph(safe, styles["urgent"]))
        else:
            elements.append(Paragraph(safe, styles["normal"]))

    elements.extend(_confidential_footer(styles))

    doc.build(elements)
    return buffer.getvalue()


def generate_deo_report_docx(content: str, report_type: str, title: str | None = None, reference: str | None = None) -> bytes:
    """Generate an editable DEO report as a DOCX file."""
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    # Letterhead
    title = doc.add_heading("GOVERNMENT OF ANDHRA PRADESH", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        run.font.size = Pt(14)

    sub = doc.add_heading("Department of School Education", level=2)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs:
        run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
        run.font.size = Pt(11)

    dept = doc.add_paragraph("District Education Officer - Governance Platform")
    dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if dept.runs:
        dept.runs[0].font.size = Pt(9)
        dept.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    # Horizontal rule
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:color"), "1D4ED8")
    pBdr.append(bottom)
    pPr.append(pBdr)
    doc.add_paragraph()

    # Report title
    report_title = title or report_type.replace("_", " ").upper()
    rtitle = doc.add_heading(report_title, level=1)
    rtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in rtitle.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        run.font.size = Pt(13)

    if reference:
        ref_p = doc.add_paragraph()
        ref_p.add_run("Ref. No.: ").bold = True
        ref_p.add_run(reference)
        date_p = doc.add_paragraph()
        date_p.add_run("Date: ").bold = True
        date_p.add_run(date.today().strftime("%d-%m-%Y"))
        doc.add_paragraph()

    # Content
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph()
            continue

        upper_words = [w for w in stripped.split() if w.isupper() and len(w) > 2]
        is_heading = (len(upper_words) >= 3) or stripped.endswith(":") or stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))

        if is_heading:
            h = doc.add_heading(stripped, level=2)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
                run.font.size = Pt(11)
        elif stripped.startswith(("•", "-", "*", "➢", "→")):
            p = doc.add_paragraph(f"• {stripped.lstrip('•-*➢→ ')}", style="List Bullet")
            if p.runs:
                p.runs[0].font.size = Pt(10)
        else:
            p = doc.add_paragraph(stripped)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if p.runs:
                p.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    footer_p = doc.add_paragraph(
        f"CONFIDENTIAL | EduAI DEO Copilot | {date.today().strftime('%d %B %Y')}"
    )
    if footer_p.runs:
        footer_p.runs[0].font.size = Pt(8)
        footer_p.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()