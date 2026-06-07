"""
Document Translation Service - extracts text from uploaded documents and translates it.

Supports: PDF, DOCX, DOC, TXT files.
Uses NVIDIA NIM through the shared OpenAI-compatible client.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.utils.gemini_client import TRANSLATION_PROMPT, generate_text

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text content from an uploaded document file.
    Supports PDF via PyMuPDF/pdfminer, DOCX via python-docx, and plain text.
    """
    contents = await file.read()
    ext = os.path.splitext(file.filename or "document.txt")[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    text = ""

    if ext == ".txt":
        text = contents.decode("utf-8", errors="replace")

    elif ext == ".pdf":
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=contents, filetype="pdf")
            try:
                text = "\n\n".join(page.get_text() for page in doc)
            finally:
                doc.close()
        except ImportError:
            try:
                from pdfminer.high_level import extract_text as pdfminer_extract

                tmp_path = ""
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(contents)
                        tmp_path = tmp.name
                    text = pdfminer_extract(tmp_path)
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except ImportError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="PDF text extraction requires PyMuPDF or pdfminer. Run: pip install PyMuPDF",
                ) from exc
        except Exception as exc:
            logger.exception("PDF extraction failed")
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(exc)[:200]}") from exc

    elif ext in {".docx", ".doc"}:
        try:
            from docx import Document

            doc = Document(io.BytesIO(contents))
            text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="DOCX text extraction requires python-docx. Run: pip install python-docx",
            ) from exc
        except Exception as exc:
            logger.exception("DOCX extraction failed")
            raise HTTPException(status_code=400, detail=f"Failed to read DOCX: {str(exc)[:200]}") from exc

    text = "\n".join(line.strip() for line in text.splitlines())
    text = "\n\n".join(para.strip() for para in text.split("\n\n") if para.strip())

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded document.")

    max_chars = 15000
    if len(text) > max_chars:
        logger.warning("Document too long (%d chars), truncating to %d chars", len(text), max_chars)
        text = text[:max_chars] + "\n\n[... Document truncated due to length ...]"

    logger.info(
        "Extracted %d characters from %s (type: %s)",
        len(text),
        file.filename or "unknown",
        ext,
    )

    return text


async def translate_document_text(
    text: str,
    source_language: str,
    target_language: str,
    document_type: str | None = None,
) -> dict[str, Any]:
    """
    Translate extracted document text using NVIDIA NIM.

    Returns translated_text and metadata.
    """
    if source_language not in {"Telugu", "English"}:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: {source_language}")
    if target_language not in {"Telugu", "English"}:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {target_language}")
    if source_language == target_language:
        raise HTTPException(status_code=400, detail="Source and target language must be different")

    doc_type_hint = f"\nDocument type: {document_type}" if document_type else ""
    prompt = TRANSLATION_PROMPT.format(
        source_language=source_language,
        target_language=target_language,
        text=f"{doc_type_hint}\n\n{text}",
    )

    try:
        translated = (await generate_text(prompt)).strip()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Document translation failed after extracting %d characters", len(text))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Document text was extracted, but AI translation failed: {str(exc)[:200]}",
        ) from exc

    if not translated:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document text was extracted, but the AI translation service returned an empty response.",
        )

    return {
        "translated_text": translated,
        "source_language": source_language,
        "target_language": target_language,
        "original_length": len(text),
        "translated_length": len(translated),
        "word_count": len(text.split()),
    }
