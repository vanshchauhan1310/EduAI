"""
PDF ingestion for the RAG knowledge base
========================================
Parse an uploaded PDF (e.g. an NCERT chapter), split it into overlapping text
chunks, and store them in SQLite (db.KBChunk). The RAG retriever (rag.py) then
indexes these chunks so the tutor's lessons/quizzes are grounded in the PDF.

Pipeline:  extract_text() -> chunk_text() -> db.add_chunks()
"""

import os
import re
from typing import List, Tuple

import fitz  # PyMuPDF — decodes NCERT custom font encodings that pypdf cannot

import db as store

CHUNK_SIZE = 900       # characters per chunk
CHUNK_OVERLAP = 150    # overlap so sentences aren't cut between chunks

# ── Local PDF store (TEST ONLY) ───────────────────────────────────────────────
# PDFs are kept here for local testing. In production, a future developer should
# replace this with object storage (S3 / Supabase Storage) and the chunks should
# live in the production DB (Postgres + pgvector) — see README.
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")


def ensure_pdf_dir() -> str:
    os.makedirs(PDF_DIR, exist_ok=True)
    return PDF_DIR


def list_pdfs() -> List[str]:
    """PDF filenames currently sitting in the local test folder."""
    ensure_pdf_dir()
    return sorted(f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf"))


def save_pdf_bytes(name: str, data: bytes) -> str:
    """Persist an uploaded PDF into the local test folder; returns its path."""
    ensure_pdf_dir()
    safe = os.path.basename(name)
    path = os.path.join(PDF_DIR, safe)
    with open(path, "wb") as f:
        f.write(data)
    return path


def path_for(name: str) -> str:
    return os.path.join(PDF_DIR, os.path.basename(name))


def extract_pages(path: str) -> List[Tuple[int, str]]:
    """Return [(page_number, text)] for each page with extractable text.
    Uses PyMuPDF (fitz), which decodes NCERT/embedded-font PDFs correctly."""
    pages = []
    doc = fitz.open(path)
    try:
        for i in range(len(doc)):
            text = doc.load_page(i).get_text() or ""
            text = re.sub(r"[ \t]+", " ", text)        # collapse runs of spaces
            text = re.sub(r"\n{3,}", "\n\n", text)     # collapse blank lines
            text = text.replace("\x00", "").strip()
            if text:
                pages.append((i + 1, text))
    finally:
        doc.close()
    return pages


# ── OCR fallback (for scanned / symbol-font PDFs) ─────────────────────────────
_ocr_engine = None


def _get_ocr():
    """Lazily load the RapidOCR engine (ONNX, CPU, no system binary)."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine


def ocr_pages(path: str, dpi: int = 170, page_start: int = 1,
              page_end: int = None, progress=None) -> List[Tuple[int, str]]:
    """Render a page range to images and OCR them. Slow (~a few s/page)."""
    import numpy as np
    engine = _get_ocr()
    pages: List[Tuple[int, str]] = []
    doc = fitz.open(path)
    try:
        first = max(1, page_start) - 1
        last = len(doc) if page_end is None else min(page_end, len(doc))
        total = max(0, last - first)
        for n, i in enumerate(range(first, last), start=1):
            pix = doc.load_page(i).get_pixmap(dpi=dpi, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n)
            result, _ = engine(img)
            text = " ".join(line[1] for line in result) if result else ""
            text = re.sub(r"[ \t]+", " ", text).strip()
            if text:
                pages.append((i + 1, text))
            if progress:
                progress(n, total)
    finally:
        doc.close()
    return pages


# A few very common English words — used to detect whether extraction produced
# real text vs. symbol-font garbage (NCERT PDFs with no Unicode font mapping).
_COMMON = {"the", "and", "is", "of", "to", "in", "a", "that", "it", "as", "for",
           "are", "with", "this", "on", "or", "by", "an", "we", "be"}


def looks_extractable(text: str) -> bool:
    """True if the extracted text looks like real English (not glyph garbage)."""
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    if len(words) < 30:
        return False
    common = sum(1 for w in words if w in _COMMON)
    return (common / len(words)) > 0.03


def chunk_text(text: str, size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping character chunks, breaking on whitespace."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        # try not to cut mid-word
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


def ingest_pdf(path: str, subject: str, chapter: str, db,
               use_ocr: bool = False, page_start: int = 1, page_end: int = None,
               progress=None) -> dict:
    """Parse a PDF and store its chunks. Returns a summary dict.
    use_ocr=True renders pages and OCRs them (for scanned/symbol-font PDFs)."""
    source = os.path.basename(path)

    if use_ocr:
        pages = ocr_pages(path, page_start=page_start, page_end=page_end, progress=progress)
        if not pages:
            return {"success": False, "source": source, "pages": 0, "chunks": 0,
                    "error": "OCR produced no text from this PDF."}
    else:
        pages = extract_pages(path)
        # Quality gate: reject scanned / symbol-font PDFs whose text is unreadable.
        full = " ".join(t for _, t in pages)
        if not looks_extractable(full):
            return {"success": False, "source": source, "pages": len(pages), "chunks": 0,
                    "error": ("Text could not be extracted — this PDF looks scanned or uses "
                              "non-standard fonts (no Unicode mapping). Try a text-based NCERT "
                              "PDF, or tick 'Use OCR' to read it (slower).")}

    page_chunks: List[Tuple[int, str]] = []
    for page_no, text in pages:
        for chunk in chunk_text(text):
            page_chunks.append((page_no, chunk))

    if not page_chunks:
        return {"success": False, "source": source, "pages": len(pages),
                "chunks": 0, "error": "No extractable text (is it a scanned PDF?)."}

    stored = store.add_chunks(db, source, subject, chapter, page_chunks)
    return {"success": True, "source": source, "pages": len(pages), "chunks": stored}


def ingest_text(text: str, source: str, subject: str, chapter: str, db) -> dict:
    """Ingest raw text (used for tests / pasting content) the same way as a PDF."""
    chunks = [(1, c) for c in chunk_text(text)]
    stored = store.add_chunks(db, source, subject, chapter, chunks)
    return {"success": True, "source": source, "pages": 1, "chunks": stored}
