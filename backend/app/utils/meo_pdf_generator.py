"""
MEO PDF and DOCX generation utility using ReportLab and python-docx.
Generates government-format MEO reports as PDF and DOCX bytes with sharing support.
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


def _letterhead(styles: dict) -> list:
    return [
        Paragraph("GOVERNMENT OF ANDHRA PRADESH", styles["header"]),
        Paragraph("Department of School Education", styles["subheader"]),
        Paragraph("Mandal Education Officer - Governance Platform", styles["small"]),
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
            f"CONFIDENTIAL | EduAI MEO Copilot | {date.today().strftime('%d %B %Y')}",
            styles["small"],
        ),
    ]


# ─── PDF Generation ───────────────────────────────────────────────

def generate_meo_report_pdf(content: str, report_type: str, reference_number: str | None = None) -> bytes:
    """Render an MEO report as a government-formatted A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    )
    styles = _base_styles()
    elements: list = []

    elements.extend(_letterhead(styles))

    # Report title based on type
    title_map = {
        "early_warning":            "EARLY WARNING BRIEFING",
        "teacher_vacancy":          "TEACHER VACANCY & DEPLOYMENT REPORT",
        "governance_communication": "GOVERNANCE COMMUNICATION - OFFICIAL CIRCULAR",
        "cluster_briefing":         "CLUSTER GOVERNANCE BRIEFING",
    }
    report_title = title_map.get(report_type, report_type.replace("_", " ").upper())

    elements.append(Paragraph(f"<b>{report_title}</b>", styles["header"]))
    elements.append(Spacer(1, 2 * mm))

    if reference_number:
        elements.append(Paragraph(f"<b>Ref. No.:</b> {reference_number}", styles["small"]))
        elements.append(Paragraph(f"<b>Date:</b> {date.today().strftime('%d-%m-%Y')}", styles["small"]))
        elements.append(Spacer(1, 4 * mm))

    # Parse content and render with appropriate styles
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            elements.append(Spacer(1, 3 * mm))
            i += 1
            continue

        # Detect section headings (all caps or ending with colon)
        upper_words = [w for w in stripped.split() if w.isupper() and len(w) > 2]
        is_heading = (len(upper_words) >= 3) or stripped.endswith(":") or stripped.startswith("1.") or stripped.startswith("2.") or stripped.startswith("3.")

        if is_heading:
            elements.append(Paragraph(f"<b>{stripped}</b>", styles["subsection"]))
        elif stripped.startswith(("•", "-", "*", "➢", "→")):
            elements.append(Paragraph(f"• {stripped.lstrip('•-*➢→ ')}", styles["bullet"]))
        elif stripped.startswith(("URGENT", "IMMEDIATE", "CRITICAL")):
            elements.append(Paragraph(stripped, styles["urgent"]))
        else:
            elements.append(Paragraph(stripped, styles["normal"]))
        i += 1

    elements.extend(_confidential_footer(styles))

    doc.build(elements)
    return buffer.getvalue()


# ─── DOCX Generation ──────────────────────────────────────────────

def _get_telugu_font():
    fonts = [
        "Noto Sans Telugu", "Segoe UI", "Cambria",
        "Calibri", "Arial Unicode MS", "DejaVu Sans", "Arial",
    ]
    return fonts


def _set_font_for_run(run, font_names=None, size: int = 11):
    if font_names is None:
        font_names = _get_telugu_font()
    if isinstance(font_names, str):
        font_names = [font_names]
    primary_font = font_names[0]
    run.font.name = primary_font
    run.font.size = Pt(size)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    try:
        rFonts.set(qn('w:ascii'), primary_font)
        rFonts.set(qn('w:hAnsi'), primary_font)
        rFonts.set(qn('w:cs'), primary_font)
    except Exception:
        pass
    try:
        rFonts.set(qn('w:eastAsia'), primary_font)
    except Exception:
        pass


def generate_school_health_pdf(report_data: dict) -> bytes:
    """Render a school health analyzer report as a formatted A4 PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2.5*cm, leftMargin=2.5*cm, topMargin=2.0*cm, bottomMargin=2.0*cm)
    styles = _base_styles()
    elements: list = []
    elements.extend(_letterhead(styles))

    elements.append(Paragraph("<b>SCHOOL HEALTH CLUSTER ANALYSIS</b>", styles["header"]))
    elements.append(Paragraph(f"Mandal: {report_data.get('mandal_name', '')}", styles["subheader"]))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d-%m-%Y')} | Schools Analyzed: {report_data.get('selected_school_count', 0)}", styles["small"]))
    elements.append(Spacer(1, 4*mm))

    # Cluster Insights
    elements.append(Paragraph("<b>Cluster Insights</b>", styles["section"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(report_data.get('cluster_insights', ''), styles["normal"]))
    elements.append(Spacer(1, 4*mm))

    # Strengths
    strengths = report_data.get('strengths', [])
    if strengths:
        elements.append(Paragraph("<b>Strengths</b>", styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        for s in strengths:
            elements.append(Paragraph(f"* {s}", styles["bullet"]))
        elements.append(Spacer(1, 4*mm))

    # Concerns
    concerns = report_data.get('concerns', [])
    if concerns:
        elements.append(Paragraph("<b>Concerns</b>", styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        for c in concerns:
            elements.append(Paragraph(f"* {c}", styles["bullet"]))
        elements.append(Spacer(1, 4*mm))

    # Recommendations
    recs = report_data.get('recommendations', [])
    if recs:
        elements.append(Paragraph("<b>Recommendations</b>", styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        for r in recs:
            elements.append(Paragraph(f"* {r}", styles["bullet"]))
        elements.append(Spacer(1, 4*mm))

    # Action Plan
    actions = report_data.get('action_plan', [])
    if actions:
        elements.append(Paragraph("<b>Action Plan</b>", styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        for a in actions:
            elements.append(Paragraph(f"* {a}", styles["bullet"]))
        elements.append(Spacer(1, 4*mm))

    # School Breakdown
    breakdown = report_data.get('school_breakdown', [])
    if breakdown:
        elements.append(Paragraph("<b>School Breakdown</b>", styles["section"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=GOV_BLUE))
        for s in breakdown:
            score = s.get('health_score', 0)
            grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
            elements.append(Paragraph(f"<b>{s.get('school_name', '')}</b> (Grade: {grade}) - Health Score: {score}", styles["subsection"]))
            elements.append(Paragraph(f"DISE: {s.get('dise_code', '')} | Students: {s.get('total_students', 0)} | Teachers: {s.get('total_teachers', 0)} | PTR: 1:{s.get('teacher_student_ratio', 0):.1f}", styles["normal"]))
            elements.append(Spacer(1, 2*mm))

    # Summary
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"<b>Top School:</b> {report_data.get('top_school', '')}", styles["success"]))
    elements.append(Paragraph(f"<b>Most At-Risk School:</b> {report_data.get('most_at_risk_school', '')}", styles["urgent"]))

    elements.extend(_confidential_footer(styles))
    doc.build(elements)
    return buffer.getvalue()


def generate_school_health_docx(report_data: dict) -> bytes:
    """Generate an editable school health analyzer report as a DOCX file."""
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    _docx_letterhead(doc)

    title_heading = doc.add_heading("SCHOOL HEALTH CLUSTER ANALYSIS", level=1)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_heading.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        _set_font_for_run(run, size=13)

    date_p = doc.add_paragraph(f"Mandal: {report_data.get('mandal_name', '')} | Schools Analyzed: {report_data.get('selected_school_count', 0)}")
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if date_p.runs:
        _set_font_for_run(date_p.runs[0], size=10)
    doc.add_paragraph()

    # Cluster Insights
    h = doc.add_heading("Cluster Insights", level=2)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
    p = doc.add_paragraph(report_data.get('cluster_insights', ''))
    if p.runs:
        _set_font_for_run(p.runs[0], size=10)
    doc.add_paragraph()

    for section_name in ['strengths', 'concerns', 'recommendations', 'action_plan']:
        items = report_data.get(section_name, [])
        if items:
            h = doc.add_heading(section_name.replace('_', ' ').title(), level=2)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
            for item in items:
                bp = doc.add_paragraph(f"* {item}", style="List Bullet")
                if bp.runs:
                    _set_font_for_run(bp.runs[0], size=10)
            doc.add_paragraph()

    # School Breakdown
    breakdown = report_data.get('school_breakdown', [])
    if breakdown:
        h = doc.add_heading("School Breakdown", level=2)
        for run in h.runs:
            run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
        for s in breakdown:
            score = s.get('health_score', 0)
            grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
            p = doc.add_paragraph()
            run = p.add_run(f"{s.get('school_name', '')} (Grade: {grade})")
            run.bold = True
            _set_font_for_run(run, size=11)
            sp = doc.add_paragraph(f"DISE: {s.get('dise_code', '')} | Students: {s.get('total_students', 0)} | Teachers: {s.get('total_teachers', 0)} | Health Score: {score}")
            if sp.runs:
                _set_font_for_run(sp.runs[0], size=10)
            doc.add_paragraph()

    footer_p = doc.add_paragraph(f"CONFIDENTIAL | EduAI School Health Analyzer | {date.today().strftime('%d %B %Y')}")
    if footer_p.runs:
        _set_font_for_run(footer_p.runs[0], size=8)
        footer_p.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
    title = doc.add_heading("GOVERNMENT OF ANDHRA PRADESH", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        _set_font_for_run(run, size=14)

    sub = doc.add_heading("Department of School Education", level=2)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs:
        run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
        _set_font_for_run(run, size=11)

    small = doc.add_paragraph("Mandal Education Officer - Governance Platform")
    small.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if small.runs:
        _set_font_for_run(small.runs[0], size=9)
        small.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

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


def generate_meo_report_docx(content: str, report_type: str, reference_number: str | None = None) -> bytes:
    """Generate an editable MEO report as a DOCX file."""
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    _docx_letterhead(doc)

    title_map = {
        "early_warning":            "EARLY WARNING BRIEFING",
        "teacher_vacancy":          "TEACHER VACANCY & DEPLOYMENT REPORT",
        "governance_communication": "GOVERNANCE COMMUNICATION - OFFICIAL CIRCULAR",
        "cluster_briefing":         "CLUSTER GOVERNANCE BRIEFING",
    }
    report_title = title_map.get(report_type, report_type.replace("_", " ").upper())
    title_heading = doc.add_heading(report_title, level=1)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_heading.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        _set_font_for_run(run, size=13)

    if reference_number:
        ref_p = doc.add_paragraph()
        ref_p.add_run("Ref. No.: ").bold = True
        ref_p.add_run(reference_number)
        date_p = doc.add_paragraph()
        date_p.add_run("Date: ").bold = True
        date_p.add_run(date.today().strftime("%d-%m-%Y"))
        doc.add_paragraph()

    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph()
            continue

        # Detect headings
        upper_words = [w for w in stripped.split() if w.isupper() and len(w) > 2]
        is_heading = (len(upper_words) >= 3) or stripped.endswith(":") or stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))

        if is_heading:
            h = doc.add_heading(stripped, level=2)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)
                _set_font_for_run(run, size=11)
        elif stripped.startswith(("•", "-", "*", "➢", "→")):
            p = doc.add_paragraph(f"• {stripped.lstrip('•-*➢→ ')}", style="List Bullet")
            if p.runs:
                _set_font_for_run(p.runs[0], size=10)
        else:
            p = doc.add_paragraph(stripped)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if p.runs:
                _set_font_for_run(p.runs[0], size=10)

    doc.add_paragraph()
    footer_p = doc.add_paragraph(
        f"CONFIDENTIAL | EduAI MEO Copilot | {date.today().strftime('%d %B %Y')}"
    )
    if footer_p.runs:
        _set_font_for_run(footer_p.runs[0], size=8)
        footer_p.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()