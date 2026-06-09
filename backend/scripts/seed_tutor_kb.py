"""
One-off seed script: ingest the bundled NCERT chapter (data/chapters/jesc101.pdf —
the Class 10 Electricity chapter) into the AI Tutor's shared knowledge base
(student_id=None — visible to every student) so RAG grounding has real textbook
content from day one, not just the curated notes.

Run from backend/:  python scripts/seed_tutor_kb.py
"""
import sys
sys.path.insert(0, ".")

import asyncio
from pathlib import Path

from sqlalchemy import select

from app.ai.tutor.pdf_ingest import ingest_pdf
from app.database.session import AsyncSessionLocal
from app.models.tutor import TutorKnowledgeChunk

PDF_PATH = Path("data") / "chapters" / "jesc101.pdf"
SUBJECT = "Physics"
CHAPTER = "Electricity"


async def seed():
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH} — nothing to seed.")
        return

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(TutorKnowledgeChunk).where(
                TutorKnowledgeChunk.student_id.is_(None),
                TutorKnowledgeChunk.source == PDF_PATH.name,
            ).limit(1)
        )
        if existing.scalar_one_or_none():
            print(f"'{PDF_PATH.name}' is already seeded as a shared source — skipping.")
            return

        result = await ingest_pdf(
            db, str(PDF_PATH), subject=SUBJECT, chapter=CHAPTER, student_id=None,
        )
        if result.get("success"):
            await db.commit()
            print(f"Seeded '{result['source']}' — {result['pages']} pages, {result['chunks']} chunks "
                  f"({SUBJECT} / {CHAPTER}, shared).")
        else:
            await db.rollback()
            print(f"Seeding failed: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(seed())
