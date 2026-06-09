# app/ai/tutor/pdf_ingest.py
"""
PDF -> chunked TutorKnowledgeChunk rows (ports prototype/pdf_ingest.py).

Pipeline: extract_pages() -> chunk_text() -> persist TutorKnowledgeChunk rows.
Reuses app.ai.exam_prep.pdf_parser.extract_text_from_pdf for the actual PyMuPDF
extraction/cleaning (rather than duplicating it) and recovers page numbers from
its "--- PAGE N ---" markers. OCR (for scanned/symbol-font PDFs) is lazily
imported exactly like the prototype's `_get_ocr` — a missing `rapidocr_onnxruntime`
only breaks OCR-flagged ingests, never normal text-PDF ingestion.
"""

import os
import re
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.exam_prep.pdf_parser import extract_text_from_pdf
from app.models.tutor import TutorKnowledgeChunk

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

_PAGE_RE = re.compile(r"-{2,}\s*PAGE\s*(\d+)\s*-{2,}")

# Common English words — used to detect whether extraction produced real text vs.
# symbol-font garbage (some NCERT PDFs have no Unicode font mapping).
_COMMON = {"the", "and", "is", "of", "to", "in", "a", "that", "it", "as", "for",
           "are", "with", "this", "on", "or", "by", "an", "we", "be"}


def extract_pages(pdf_path: str) -> List[Tuple[int, str]]:
    """[(page_number, text)] — recovered from extract_text_from_pdf's page markers."""
    full_text = extract_text_from_pdf(pdf_path)
    parts = _PAGE_RE.split(full_text)
    pages: List[Tuple[int, str]] = []
    for i in range(1, len(parts), 2):
        text = parts[i + 1].strip()
        if text:
            pages.append((int(parts[i]), text))
    return pages


# ── OCR fallback (lazy import — see module docstring) ────────────────────────
_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine


def ocr_pages(path: str, dpi: int = 170, page_start: int = 1,
              page_end: Optional[int] = None) -> List[Tuple[int, str]]:
    """Render a page range to images and OCR them. Slow (~a few s/page)."""
    import numpy as np
    engine = _get_ocr()
    pages: List[Tuple[int, str]] = []
    doc = fitz.open(path)
    try:
        first = max(1, page_start) - 1
        last = len(doc) if page_end is None else min(page_end, len(doc))
        for i in range(first, last):
            pix = doc.load_page(i).get_pixmap(dpi=dpi, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            result, _ = engine(img)
            text = " ".join(line[1] for line in result) if result else ""
            text = re.sub(r"[ \t]+", " ", text).strip()
            if text:
                pages.append((i + 1, text))
    finally:
        doc.close()
    return pages


def looks_extractable(text: str) -> bool:
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    if len(words) < 30:
        return False
    common = sum(1 for w in words if w in _COMMON)
    return (common / len(words)) > 0.03


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Overlapping character chunks, breaking on whitespace so sentences survive."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            sp = text.rfind(" ", start + size - overlap, end)
            if sp != -1:
                end = sp
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


async def ingest_pdf(
    db: AsyncSession,
    path: str,
    subject: str,
    chapter: str,
    student_id: Optional[int],
    use_ocr: bool = False,
    page_start: int = 1,
    page_end: Optional[int] = None,
) -> dict:
    """Parse a PDF, chunk it and persist TutorKnowledgeChunk rows. Returns a
    summary dict {success, source, pages, chunks, error?}.
    `student_id=None` means a shared/seeded source (visible to every student);
    otherwise the chunks are private to that student ("My Study Material")."""
    source = os.path.basename(path)

    if use_ocr:
        pages = ocr_pages(path, page_start=page_start, page_end=page_end)
        if not pages:
            return {"success": False, "source": source, "pages": 0, "chunks": 0,
                    "error": "OCR produced no text from this PDF."}
    else:
        pages = extract_pages(path)
        full = " ".join(text for _, text in pages)
        if not looks_extractable(full):
            return {"success": False, "source": source, "pages": len(pages), "chunks": 0,
                    "error": ("Text could not be extracted — this PDF looks scanned or uses "
                              "non-standard fonts (no Unicode mapping). Try a text-based NCERT "
                              "PDF, or enable OCR (slower).")}

    rows: List[TutorKnowledgeChunk] = []
    for page_no, text in pages:
        for chunk in chunk_text(text):
            rows.append(TutorKnowledgeChunk(
                student_id=student_id, source=source, page=page_no,
                subject=subject, chapter=chapter, text=chunk,
            ))

    if not rows:
        return {"success": False, "source": source, "pages": len(pages),
                "chunks": 0, "error": "No extractable text (is it a scanned PDF?)."}

    db.add_all(rows)
    await db.flush()
    return {"success": True, "source": source, "pages": len(pages), "chunks": len(rows)}
