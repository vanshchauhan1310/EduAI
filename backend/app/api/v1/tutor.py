from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.tutor import (
    ChatRequest,
    ChatResponse,
    ConceptMasteryOut,
    GradeQuizRequest,
    IngestResultOut,
    KnowledgeBaseSourceOut,
    QuizGradeResponse,
    RagSourceOut,
    TutorGenerateRequest,
    TutorGenerateResponse,
)
from app.services.tutor_service import get_tutor_service

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

tutor_service = get_tutor_service()


async def _resolve_student(current_user: User, db: AsyncSession) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can access the AI Tutor")
    return student


@router.post("/generate", response_model=TutorGenerateResponse)
async def generate_lesson(
    request: TutorGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.generate_lesson(db, student, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/grade", response_model=QuizGradeResponse)
async def grade_quiz(
    request: GradeQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.grade_quiz(db, student, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery", response_model=ConceptMasteryOut)
async def get_mastery(
    subject: str = Query(...),
    concept: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.get_mastery(db, student, subject, concept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/recent", response_model=list[ConceptMasteryOut])
async def get_recent_concepts(
    limit: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.get_recent_concepts(db, student, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.chat(db, student, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/ingest", response_model=IngestResultOut)
async def ingest_pdf(
    file: UploadFile = File(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    use_ocr: bool = Form(False),
    page_start: int = Form(1),
    page_end: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.ingest_pdf(
            db, student, file, subject=subject, chapter=chapter,
            use_ocr=use_ocr, page_start=page_start, page_end=page_end,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/sources", response_model=list[KnowledgeBaseSourceOut])
async def get_knowledge_base_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.get_kb_sources(db, student)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/search", response_model=list[RagSourceOut])
async def search_knowledge_base(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await _resolve_student(current_user, db)
    try:
        return await tutor_service.search_kb(db, student, q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
