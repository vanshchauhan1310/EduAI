"""
DOCX generation utility using python-docx.
Generates editable Word documents for letters and reports.
"""
from io import BytesIO
from datetime import date
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _get_telugu_font():
    """Get best available font for Telugu script with fallback chain."""
    # Fonts in order of preference for Telugu support
    fonts = [
        "Noto Sans Telugu",
        "Segoe UI",
        "Cambria",
        "Calibri",
        "Arial Unicode MS",
        "DejaVu Sans",
        "Arial",
    ]

    # Try to detect installed font files (Windows / macOS / Linux)
    try:
        from pathlib import Path
        candidates = [
            Path("C:/Windows/Fonts"),
            Path("/usr/share/fonts"),
            Path(os.path.expanduser("~/Library/Fonts")),
        ]
        found = []
        for base in candidates:
            if not base or not base.exists():
                continue
            for f in base.rglob("*.ttf"):
                lf = f.name.lower()
                if "telugu" in lf or "noto" in lf and "telugu" in lf:
                    found.append(f)
        # If a Noto Sans Telugu file exists, prefer the Noto family
        if found:
            return ["Noto Sans Telugu"] + [f for f in fonts if f != "Noto Sans Telugu"]
    except Exception:
        pass

    return fonts  # Return list for Word to handle fallback


def _set_font_for_run(run, font_names=None, size: int = 11):
    """Set Telugu-compatible font for a text run with fallback chain."""
    if font_names is None:
        font_names = _get_telugu_font()
    
    # If single font string provided, convert to list
    if isinstance(font_names, str):
        font_names = [font_names]
    
    primary_font = font_names[0]
    run.font.name = primary_font
    run.font.size = Pt(size)

    # Set rFonts element for proper font fallback with multiple fonts
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)

    # Set primary font for different script slots
    try:
        rFonts.set(qn('w:ascii'), primary_font)
        rFonts.set(qn('w:hAnsi'), primary_font)
        rFonts.set(qn('w:cs'), primary_font)
    except Exception:
        pass

    # Also set eastAsia slot (harmless if not used) and let Word fallback to other fonts
    try:
        rFonts.set(qn('w:eastAsia'), primary_font)
    except Exception:
        pass


GOV_BLUE = RGBColor(0x1D, 0x4E, 0xD8)
GOV_DARK = RGBColor(0x1E, 0x3A, 0x8A)


def _set_heading_color(paragraph, color: RGBColor):
    for run in paragraph.runs:
        run.font.color.rgb = color
        _set_font_for_run(run, size=int(run.font.size.pt) if run.font.size else 11)


def _add_horizontal_rule(doc: Document):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:color"), "1D4ED8")
    pBdr.append(bottom)
    pPr.append(pBdr)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)


def _letterhead(doc: Document):
    title = doc.add_heading("GOVERNMENT OF ANDHRA PRADESH", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_heading_color(title, GOV_DARK)

    sub = doc.add_heading("Department of School Education", level=2)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_heading_color(sub, GOV_BLUE)

    small = doc.add_paragraph("Education Governance Platform")
    small.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if small.runs:
        _set_font_for_run(small.runs[0], size=9)
        small.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    _add_horizontal_rule(doc)
    doc.add_paragraph()


def generate_letter_docx(letter_content: str, reference_number: str | None = None) -> bytes:
    """Generate an editable government letter as a DOCX file."""
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    _letterhead(doc)

    if reference_number:
        ref_p = doc.add_paragraph()
        ref_p.add_run("Ref. No.: ").bold = True
        ref_p.add_run(reference_number)
        date_p = doc.add_paragraph()
        date_p.add_run("Date: ").bold = True
        date_p.add_run(date.today().strftime("%d-%m-%Y"))
        doc.add_paragraph()

    for line in letter_content.split("\n"):
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph()
            continue
        if stripped.startswith(("Subject:", "To:", "From:")):
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            _set_font_for_run(run, size=11)
        elif stripped.startswith(("•", "-", "*")):
            p = doc.add_paragraph(f"• {stripped.lstrip('•-* ')}", style="List Bullet")
            if p.runs:
                _set_font_for_run(p.runs[0], size=10)
        else:
            p = doc.add_paragraph(stripped)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if p.runs:
                _set_font_for_run(p.runs[0], size=10)

    doc.add_paragraph()
    footer_p = doc.add_paragraph(
        f"Generated by EduAI Admin Copilot | {date.today().strftime('%d %B %Y')}"
    )
    if footer_p.runs:
        _set_font_for_run(footer_p.runs[0], size=8)
        footer_p.runs[0].font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_report_docx(report_type: str, content: str, content_json: dict | None = None) -> bytes:
    """Generate an editable report as a DOCX file."""
    doc = Document()

    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    _letterhead(doc)

    title_heading = doc.add_heading(report_type.replace("_", " ").upper(), level=1)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_heading_color(title_heading, GOV_DARK)

    date_p = doc.add_paragraph(f"Generated: {date.today().strftime('%d %B %Y')}")
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if date_p.runs:
        _set_font_for_run(date_p.runs[0], size=9)
    doc.add_paragraph()

    if content_json:
        section_map = {
            "executive_summary": "Executive Summary",
            "kpi_analysis":       "KPI Analysis",
            "trends":             "Trends & Observations",
            "risks":              "Risk Areas",
            "recommendations":    "Recommendations",
            "action_plan":        "Action Plan",
        }
        for key, heading_text in section_map.items():
            val = content_json.get(key)
            if not val:
                continue
            h = doc.add_heading(heading_text, level=2)
            _set_heading_color(h, GOV_BLUE)
            _add_horizontal_rule(doc)
            if isinstance(val, list):
                for item in val:
                    p = doc.add_paragraph(f"• {item}", style="List Bullet")
                    if p.runs:
                        _set_font_for_run(p.runs[0], size=10)
            else:
                p = doc.add_paragraph(str(val))
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                if p.runs:
                    _set_font_for_run(p.runs[0], size=10)
            doc.add_paragraph()
    else:
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                doc.add_paragraph()
            else:
                doc.add_paragraph(stripped)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
