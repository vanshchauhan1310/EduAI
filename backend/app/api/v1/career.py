import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.student import Student
from app.models.career import CareerRecommendation
from app.services.career_recommender_service import (
    SURVEY_QUESTIONS,
    aggregate_student_signals,
    generate_recommendation,
)

router = APIRouter(prefix="/career", tags=["Career Recommender"])


class SurveyResponseItem(BaseModel):
    question_id: str
    answer: str


class SurveySubmitRequest(BaseModel):
    responses: list[SurveyResponseItem]


async def _resolve_student(current_user: User, db: AsyncSession) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can access the career recommender")
    return student


async def _get_or_create_record(db: AsyncSession, student: Student) -> CareerRecommendation:
    result = await db.execute(select(CareerRecommendation).where(CareerRecommendation.student_id == student.id))
    record = result.scalar_one_or_none()
    if not record:
        record = CareerRecommendation(student_id=student.id)
        db.add(record)
        await db.flush()
    return record


@router.get("/survey")
async def get_survey(current_user: User = Depends(get_current_user)):
    """Static aptitude/interest survey questions."""
    return {"questions": SURVEY_QUESTIONS}


@router.post("/survey")
async def submit_survey(
    request: SurveySubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persist the student's survey responses (upsert — one row per student)."""
    if not request.responses:
        raise HTTPException(status_code=400, detail="Submit at least one survey response")

    student = await _resolve_student(current_user, db)
    record = await _get_or_create_record(db, student)
    record.survey_responses_json = json.dumps([r.dict() for r in request.responses])
    await db.flush()

    return {"status": "SAVED", "responses_count": len(request.responses)}


@router.post("/recommendations/generate")
async def generate_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate real academic/attendance signals + survey answers and ask the AI for recommendations."""
    student = await _resolve_student(current_user, db)
    record = await _get_or_create_record(db, student)

    if not record.survey_responses_json:
        raise HTTPException(status_code=400, detail="Complete the career survey first")

    survey_responses = json.loads(record.survey_responses_json)
    signals = await aggregate_student_signals(db, student)
    recommendation = await generate_recommendation(student, survey_responses, signals)

    record.recommendation_json = json.dumps(recommendation)
    record.generated_at = datetime.now(timezone.utc)
    await db.flush()

    return recommendation


@router.get("/recommendations/me")
async def get_my_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single state-machine endpoint the results screen polls on load."""
    student = await _resolve_student(current_user, db)
    result = await db.execute(select(CareerRecommendation).where(CareerRecommendation.student_id == student.id))
    record = result.scalar_one_or_none()

    if not record:
        return {"survey_completed": False, "has_recommendation": False, "generated_at": None, "recommendation": None}

    return {
        "survey_completed": bool(record.survey_responses_json),
        "has_recommendation": bool(record.recommendation_json),
        "generated_at": record.generated_at.isoformat() if record.generated_at else None,
        "recommendation": json.loads(record.recommendation_json) if record.recommendation_json else None,
    }
