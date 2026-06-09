"""
AI Tutor service layer — mirrors assessment_service.py's shape: a module-level
singleton, methods that return plain dicts, ValueError -> 404 / generic -> 500
mapping handled by the router.

Wires together the app.ai.tutor.* engines (lesson/quiz generation, grading,
RAG retrieval, chat, PDF ingestion, concept images) with the DB-backed
ConceptMastery / TutorKnowledgeChunk models.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tutor import curriculum, image_search
from app.ai.tutor.image_search import _wants_image, _wants_video, search_concept_videos
from app.ai.tutor.chat_engine import get_tutor_chat
from app.ai.tutor.grading import grade, progress_decision, update_mastery
from app.ai.tutor.lesson_engine import get_lesson_engine
from app.ai.tutor.pdf_ingest import ingest_pdf as run_pdf_ingest
from app.ai.tutor.retriever import get_retriever, rebuild_index
from app.models.student import Student
from app.models.tutor import DEFAULT_MASTERY, ConceptMastery, TutorKnowledgeChunk

UPLOAD_DIR = Path("data") / "tutor_uploads"
GENERAL_TOPIC = "general Class 10"


def _source_kind(source: str) -> str:
    return "note" if source == "notes" else "pdf"


def _rag_source_out(entry: Dict) -> Dict:
    return {
        "kind": _source_kind(entry.get("source", "")),
        "concept": entry.get("concept", ""),
        "text": entry.get("text", ""),
        "score": float(entry.get("score", 0.0)),
        "source": entry.get("source") if entry.get("source") != "notes" else None,
    }


def _level_and_iso(mastery: float, updated_at) -> Dict:
    return {
        "mastery": mastery,
        "level": curriculum.level_for(mastery),
        "updated_at": updated_at,
    }


class TutorService:
    def __init__(self):
        self.lesson_engine = get_lesson_engine
        self.chat_engine = get_tutor_chat

    # ── Mastery (server-authoritative) ───────────────────────────────────────
    async def _get_mastery_row(self, db: AsyncSession, student: Student,
                               subject: str, chapter: str, concept: str) -> Optional[ConceptMastery]:
        stmt = select(ConceptMastery).where(
            ConceptMastery.student_id == student.id,
            ConceptMastery.subject == subject,
            ConceptMastery.chapter == chapter,
            ConceptMastery.concept == concept,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_mastery_row(self, db: AsyncSession, student: Student,
                                         subject: str, chapter: str, concept: str) -> ConceptMastery:
        row = await self._get_mastery_row(db, student, subject, chapter, concept)
        if row is None:
            row = ConceptMastery(student_id=student.id, subject=subject, chapter=chapter,
                                 concept=concept, mastery=DEFAULT_MASTERY)
            db.add(row)
            await db.flush()
        return row

    async def get_mastery(self, db: AsyncSession, student: Student, subject: str, concept: str) -> Dict:
        chapter = curriculum.find_chapter(subject, concept) or ""
        row = None
        if chapter:
            row = await self._get_mastery_row(db, student, subject, chapter, concept)
        if row is None:
            return {"subject": subject, "chapter": chapter, "concept": concept,
                    **_level_and_iso(DEFAULT_MASTERY, None)}
        return {"subject": row.subject, "chapter": row.chapter, "concept": row.concept,
                **_level_and_iso(row.mastery, row.updated_at)}

    async def get_recent_concepts(self, db: AsyncSession, student: Student, limit: int = 5) -> List[Dict]:
        stmt = (
            select(ConceptMastery)
            .where(ConceptMastery.student_id == student.id)
            .order_by(ConceptMastery.updated_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [
            {"subject": row.subject, "chapter": row.chapter, "concept": row.concept,
             **_level_and_iso(row.mastery, row.updated_at)}
            for row in result.scalars().all()
        ]

    # ── Lesson + quiz generation ──────────────────────────────────────────────
    async def generate_lesson(self, db: AsyncSession, student: Student, params: Dict) -> Dict:
        subject, chapter, concept = params["subject"], params["chapter"], params["concept"]

        mastery_row = await self._get_or_create_mastery_row(db, student, subject, chapter, concept)
        mastery = mastery_row.mastery

        retriever = get_retriever(student.id)
        grounding = await retriever.grounding(db, subject, chapter, concept, k=4)
        rag_text = "\n\n".join(f"[{g['concept']}] {g['text']}" for g in grounding)

        engine = self.lesson_engine()
        result, images = await asyncio.gather(
            asyncio.to_thread(
                engine.generate,
                subject=subject, chapter=chapter, concept=concept, mastery=mastery,
                language=params.get("language", "both"), rag_content=rag_text,
                num_questions=params.get("num_questions", 10),
                q_types=params.get("question_types") or ["MCQ"],
            ),
            asyncio.to_thread(
                image_search.search_concept_images,
                concept,
                user_requested_image=True,
            ),
        )

        return {
            **result,
            "rag_sources": [_rag_source_out(g) for g in grounding],
            "mastery": mastery,
            "images": images,
        }

    # ── Stateless quiz grading + mastery update ──────────────────────────────
    async def grade_quiz(self, db: AsyncSession, student: Student, params: Dict) -> Dict:
        subject, chapter, concept = params["subject"], params["chapter"], params["concept"]
        quiz = [item if isinstance(item, dict) else item.model_dump() for item in params["quiz"]]
        answers = params.get("answers") or {}

        graded = grade(quiz, answers)
        decision = progress_decision(graded, subject, chapter, concept)

        mastery_row = await self._get_or_create_mastery_row(db, student, subject, chapter, concept)
        old_mastery = mastery_row.mastery
        new_mastery = update_mastery(old_mastery, graded["percentage"])
        mastery_row.mastery = new_mastery
        await db.flush()

        results = [
            {"index": r["index"], "question": r["question"], "type": r["type"],
             "is_correct": r["is_correct"], "correct_answer": r["correct_answer"],
             "explanation": r["explanation"]}
            for r in graded["results"]
        ]

        return {
            "correct": graded["correct"], "scored": graded["scored"], "percentage": graded["percentage"],
            "results": results, "passed": decision["passed"], "message": decision["message"],
            "next_concept": decision["next_concept"], "review_topics": decision["review_topics"],
            "old_mastery": old_mastery, "new_mastery": new_mastery,
        }

    # ── Chat ──────────────────────────────────────────────────────────────────
    async def chat(self, db: AsyncSession, student: Student, params: Dict) -> Dict:
        history = [(m.get("role", "user"), m.get("content", "")) for m in (params.get("history") or [])]
        answer, detected_topic, sources = await self.chat_engine().reply(
            db, student.id, params["question"], language=params.get("language", "english"), history=history,
        )
        question = params.get("question", "")
        user_wants_image = _wants_image(question)
        user_wants_video = _wants_video(question)

        # The language picker (English/Telugu/Both) only governs the answer's
        # language — it must not change whether recommendations get attached, so
        # fall back to the question itself when no specific topic was detected.
        media_topic = detected_topic if detected_topic != GENERAL_TOPIC else question.strip()[:80]

        images = image_search.search_concept_images(
            detected_topic,
            user_requested_image=user_wants_image,
        ) if detected_topic != GENERAL_TOPIC else []

        videos = search_concept_videos(media_topic) if user_wants_video and media_topic else []

        return {
            "answer": answer,
            "detected_topic": detected_topic,
            "sources": [
                {"kind": _source_kind(s.get("source", "")), "concept": s.get("concept", ""),
                 "text": s.get("text", ""), "score": float(s.get("score", 0.0))}
                for s in sources
            ],
            "images": images,
            "videos": videos,
        }

    # ── Knowledge base / "My Study Material" ─────────────────────────────────
    async def ingest_pdf(self, db: AsyncSession, student: Student, file: UploadFile,
                         subject: str, chapter: str, use_ocr: bool = False,
                         page_start: int = 1, page_end: Optional[int] = None) -> Dict:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported for knowledge-base ingestion.")

        student_dir = UPLOAD_DIR / str(student.id)
        student_dir.mkdir(parents=True, exist_ok=True)
        safe_name = os.path.basename(file.filename)
        dest_path = student_dir / safe_name

        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        try:
            result = await run_pdf_ingest(
                db, str(dest_path), subject=subject, chapter=chapter, student_id=student.id,
                use_ocr=use_ocr, page_start=page_start, page_end=page_end,
            )
        except Exception as exc:
            dest_path.unlink(missing_ok=True)
            raise ValueError(f"Failed to process PDF: {exc}") from exc

        if not result.get("success"):
            dest_path.unlink(missing_ok=True)
            return result

        await db.flush()
        await rebuild_index(db, student.id)
        return result

    async def get_kb_sources(self, db: AsyncSession, student: Student) -> List[Dict]:
        stmt = select(TutorKnowledgeChunk).where(
            (TutorKnowledgeChunk.student_id.is_(None)) | (TutorKnowledgeChunk.student_id == student.id)
        )
        result = await db.execute(stmt)
        groups: Dict[tuple, Dict] = {}
        for chunk in result.scalars().all():
            key = (chunk.source, chunk.subject, chunk.chapter, chunk.student_id)
            entry = groups.setdefault(key, {
                "id": f"{chunk.student_id or 'shared'}-{chunk.source}-{chunk.subject}-{chunk.chapter}",
                "source": chunk.source, "subject": chunk.subject, "chapter": chunk.chapter,
                "chunks": 0, "uploaded_at": chunk.created_at,
            })
            entry["chunks"] += 1
            if chunk.created_at and (entry["uploaded_at"] is None or chunk.created_at < entry["uploaded_at"]):
                entry["uploaded_at"] = chunk.created_at

        sources = list(groups.values())
        sources.sort(key=lambda s: s["uploaded_at"] or datetime.now(timezone.utc), reverse=True)
        return sources

    async def search_kb(self, db: AsyncSession, student: Student, query: str, k: int = 8) -> List[Dict]:
        if not query.strip():
            return []
        entries = await get_retriever(student.id).retrieve(db, query, k=k)
        return [_rag_source_out(entry) for entry in entries]


_service: Optional[TutorService] = None


def get_tutor_service() -> TutorService:
    global _service
    if _service is None:
        _service = TutorService()
    return _service
