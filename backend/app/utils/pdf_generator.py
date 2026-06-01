"""
PDF generation utility using ReportLab.
Generates government-format letters and reports as PDF bytes.
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
import os


# ─── Government colour palette ────────────────────────────────────
GOV_BLUE   = colors.HexColor("#1d4ed8")
GOV_DARK   = colors.HexColor("#1e3a8a")
LIGHT_GRAY = colors.HexColor("#f3f4f6")
MID_GRAY   = colors.HexColor("#6b7280")


# ─── Register Telugu-compatible fonts ────────────────────────────
def _register_fonts():
    """Register fonts that support Telugu and other Indic scripts."""
    # Search common system font directories for Telugu-capable TTFs and register them.
    search_dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/opentype",
        "/System/Library/Fonts",
        "C:\\Windows\\Fonts",
    ]

    # Helper tokens to look for in filenames that likely support Telugu
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

    # Also try a few common explicit paths (legacy fallback)
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
    # Try to use a font that supports Telugu, with fallback chain
    # Inspect registered fonts and pick a suitable pair
    registered = set(pdfmetrics.getRegisteredFontNames())

    # Preferred families (regular, bold)
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
        "header":  ParagraphStyle("header",  fontSize=14, fontName=body_bold_font,
                                   textColor=GOV_DARK,   alignment=TA_CENTER,  spaceAfter=4),
        "subheader": ParagraphStyle("subhdr", fontSize=11, fontName=body_bold_font,
                                     textColor=GOV_BLUE,  alignment=TA_CENTER, spaceAfter=2),
        "normal":  ParagraphStyle("normal",  fontSize=10, fontName=body_font,
                                   leading=14, spaceAfter=6, alignment=TA_JUSTIFY),
        "small":   ParagraphStyle("small",   fontSize=8,  fontName=body_font,
                                   textColor=MID_GRAY),
        "section": ParagraphStyle("section", fontSize=11, fontName=body_bold_font,
                                   textColor=GOV_DARK,  spaceAfter=4, spaceBefore=12),
        "bullet":  ParagraphStyle("bullet",  fontSize=10, fontName=body_font,
                                   leading=14, leftIndent=16, spaceAfter=3),
    }


def _letterhead(styles: dict) -> list:
    elements = [
        Paragraph("GOVERNMENT OF ANDHRA PRADESH", styles["header"]),
        Paragraph("Department of School Education", styles["subheader"]),
        Paragraph("Education Governance Platform", styles["small"]),
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=2, color=GOV_BLUE),
        HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE),
        Spacer(1, 4 * mm),
    ]
    return elements


def generate_letter_pdf(letter_content: str, reference_number: str | None = None) -> bytes:
    """Render a letter string as a government-formatted A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    )
    styles = _base_styles()
    elements: list = []

    # Letterhead
    elements.extend(_letterhead(styles))

    if reference_number:
        elements.append(Paragraph(f"<b>Ref. No.:</b> {reference_number}", styles["small"]))
        elements.append(Paragraph(f"<b>Date:</b> {date.today().strftime('%d-%m-%Y')}", styles["small"]))
        elements.append(Spacer(1, 4 * mm))

    # Parse letter lines into paragraphs
    for line in letter_content.split("\n"):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 3 * mm))
            continue
        if stripped.startswith("Subject:") or stripped.startswith("To:") or stripped.startswith("From:"):
            elements.append(Paragraph(f"<b>{stripped}</b>", styles["normal"]))
        elif stripped.startswith(("•", "-", "*")):
            elements.append(Paragraph(f"• {stripped.lstrip('•-* ')}", styles["bullet"]))
        else:
            elements.append(Paragraph(stripped, styles["normal"]))

    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"Generated by EduAI Admin Copilot | {date.today().strftime('%d %B %Y')}",
        styles["small"],
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_report_pdf(report_type: str, content: str, content_json: dict | None = None) -> bytes:
    """Render an analytics report as a structured A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    )
    styles = _base_styles()
    elements: list = []

    # Letterhead
    elements.extend(_letterhead(styles))

    # Report title
    title = report_type.replace("_", " ").title()
    elements.append(Paragraph(f"<b>{title}</b>", styles["header"]))
    elements.append(Paragraph(f"Generated: {date.today().strftime('%d %B %Y')}", styles["small"]))
    elements.append(Spacer(1, 6 * mm))

    if content_json:
        section_map = {
            "executive_summary": "Executive Summary",
            "kpi_analysis":       "KPI Analysis",
            "trends":             "Trends & Observations",
            "risks":              "Risk Areas",
            "recommendations":    "Recommendations",
            "action_plan":        "Action Plan",
        }
        for key, heading in section_map.items():
            val = content_json.get(key)
            if not val:
                continue
            elements.append(Paragraph(heading, styles["section"]))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
            elements.append(Spacer(1, 2 * mm))
            if isinstance(val, list):
                for item in val:
                    elements.append(Paragraph(f"• {item}", styles["bullet"]))
            else:
                elements.append(Paragraph(str(val), styles["normal"]))
            elements.append(Spacer(1, 4 * mm))
    else:
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                elements.append(Spacer(1, 3 * mm))
            else:
                elements.append(Paragraph(stripped, styles["normal"]))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"Confidential | EduAI Admin Copilot | {date.today().strftime('%d %B %Y')}",
        styles["small"],
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_summary_pdf(file_name: str, summary_json: dict) -> bytes:
    """Render a circular summary as a structured A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    )
    styles = _base_styles()
    elements: list = []

    elements.extend(_letterhead(styles))
    elements.append(Paragraph("CIRCULAR SUMMARY REPORT", styles["header"]))
    elements.append(Paragraph(f"Source: {file_name}", styles["small"]))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d %B %Y')}", styles["small"]))
    elements.append(Spacer(1, 6 * mm))

    section_map = {
        "summary":                "Executive Summary",
        "key_instructions":       "Key Instructions",
        "action_items":           "Action Items",
        "deadlines":              "Deadlines",
        "responsible_officers":   "Responsible Officers",
        "compliance_requirements": "Compliance Requirements",
    }

    for key, heading in section_map.items():
        val = summary_json.get(key)
        if not val:
            continue
        elements.append(Paragraph(heading, styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        elements.append(Spacer(1, 2 * mm))
        if isinstance(val, list):
            for item in val:
                elements.append(Paragraph(f"• {item}", styles["bullet"]))
        else:
            elements.append(Paragraph(str(val), styles["normal"]))
        elements.append(Spacer(1, 4 * mm))

    doc.build(elements)
    return buffer.getvalue()
