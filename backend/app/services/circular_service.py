"""
Circular Summarization Service.
Extracts text from PDF using PyMuPDF, sends to NVIDIA NIM, stores result.
"""
import fitz  # PyMuPDF
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.copilot import CircularSummary
from app.models.user import User
from app.schemas.copilot import CircularSummaryJSON, CircularSummaryResponse, CircularSummaryListItem
from app.utils.gemini_client import generate_json, CIRCULAR_SUMMARY_PROMPT
from app.utils.pdf_generator import generate_summary_pdf


MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


async def _extract_pdf_text(file: UploadFile) -> tuple[str, int]:
    """Read UploadFile bytes, open with PyMuPDF, return (full_text, size_kb)."""
    content = await file.read()
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds 20 MB limit")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            text_parts = [page.get_text("text") for page in doc]
        full_text = "\n".join(text_parts).strip()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}")

    if len(full_text) < 50:
        raise HTTPException(status_code=422, detail="PDF appears to have no readable text (may be a scanned image)")

    size_kb = len(content) // 1024
    return full_text, size_kb


class CircularService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summarize(self, file: UploadFile, user: User) -> CircularSummaryResponse:
        raw_text, size_kb = await _extract_pdf_text(file)

        # Trim very long circulars to avoid token overflow (keep first 12 000 chars)
        trimmed = raw_text[:12_000]

        prompt = CIRCULAR_SUMMARY_PROMPT.format(text=trimmed)
        summary_dict = await generate_json(prompt)

        # Validate schema
        try:
            summary_obj = CircularSummaryJSON(**summary_dict)
        except Exception:
            # If the model returned partial JSON, build a graceful response
            summary_obj = CircularSummaryJSON(
                summary=summary_dict.get("summary", "Summary not available"),
                key_instructions=summary_dict.get("key_instructions", []),
                action_items=summary_dict.get("action_items", []),
                deadlines=summary_dict.get("deadlines", []),
                responsible_officers=summary_dict.get("responsible_officers", []),
                compliance_requirements=summary_dict.get("compliance_requirements", []),
            )

        record = CircularSummary(
            user_id=user.id,
            file_name=file.filename or "circular.pdf",
            file_size_kb=size_kb,
            raw_text_preview=raw_text[:500],
            summary_json=summary_obj.model_dump(),
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return CircularSummaryResponse(
            id=record.id,
            file_name=record.file_name,
            summary_json=summary_obj,
            created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20) -> list[CircularSummaryListItem]:
        result = await self.db.execute(
            select(CircularSummary)
            .where(CircularSummary.user_id == user.id)
            .order_by(desc(CircularSummary.created_at))
            .limit(limit)
        )
        records = result.scalars().all()
        return [
            CircularSummaryListItem(
                id=r.id,
                file_name=r.file_name,
                summary_preview=r.summary_json.get("summary", "")[:120] + "…",
                created_at=str(r.created_at),
            )
            for r in records
        ]

    async def get_by_id(self, summary_id: int, user: User) -> CircularSummaryResponse:
        result = await self.db.execute(
            select(CircularSummary).where(
                CircularSummary.id == summary_id,
                CircularSummary.user_id == user.id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Summary not found")
        return CircularSummaryResponse(
            id=record.id,
            file_name=record.file_name,
            summary_json=CircularSummaryJSON(**record.summary_json),
            created_at=str(record.created_at),
        )

    async def export_pdf(self, summary_id: int, user: User) -> bytes:
        resp = await self.get_by_id(summary_id, user)
        return generate_summary_pdf(resp.file_name, resp.summary_json.model_dump())
