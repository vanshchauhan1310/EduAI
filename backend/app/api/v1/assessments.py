from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResult, AssessmentType

router = APIRouter(prefix="/assessments", tags=["Assessments"])


class AssessmentCreateRequest(BaseModel):
    title: str
    assessment_type: AssessmentType
    subject: str
    class_grade: int
    section: str | None = None
    school_id: int
    academic_year: str
    max_marks: float
    passing_marks: float | None = None
    duration_minutes: int | None = None
    description: str | None = None


class GradeSubmitItem(BaseModel):
    student_id: int
    marks_obtained: float | None = None
    is_absent: bool = False
    teacher_feedback: str | None = None


class GradeSubmitRequest(BaseModel):
    results: list[GradeSubmitItem]


def calculate_grade(percentage: float) -> str:
    if percentage >= 90: return "A+"
    if percentage >= 80: return "A"
    if percentage >= 70: return "B+"
    if percentage >= 60: return "B"
    if percentage >= 50: return "C"
    if percentage >= 35: return "D"
    return "F"


@router.post("/", status_code=201)
async def create_assessment(
    request: AssessmentCreateRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assessment."""
    assessment = Assessment(
        title=request.title,
        assessment_type=request.assessment_type,
        subject=request.subject,
        class_grade=request.class_grade,
        section=request.section,
        school_id=request.school_id,
        teacher_id=current_user.teacher_profile.id if hasattr(current_user, 'teacher_profile') else 1,
        academic_year=request.academic_year,
        max_marks=request.max_marks,
        passing_marks=request.passing_marks,
        duration_minutes=request.duration_minutes,
        description=request.description,
    )
    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)
    return {"id": assessment.id, "title": assessment.title, "created": True}


@router.get("/school/{school_id}")
async def list_school_assessments(
    school_id: int,
    class_grade: int | None = Query(None),
    subject: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all assessments for a school."""
    query = select(Assessment).where(Assessment.school_id == school_id)
    if class_grade:
        query = query.where(Assessment.class_grade == class_grade)
    if subject:
        query = query.where(Assessment.subject == subject)
    result = await db.execute(query.order_by(Assessment.created_at.desc()))
    assessments = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "type": a.assessment_type.value,
            "subject": a.subject,
            "class_grade": a.class_grade,
            "max_marks": a.max_marks,
            "is_published": a.is_published,
        }
        for a in assessments
    ]


@router.post("/{assessment_id}/grade")
async def submit_grades(
    assessment_id: int,
    request: GradeSubmitRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Submit grades for an assessment."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    saved = []
    for item in request.results:
        pct = None
        grade = None
        if item.marks_obtained is not None and not item.is_absent:
            pct = round((item.marks_obtained / assessment.max_marks) * 100, 2)
            grade = calculate_grade(pct)

        result_obj = AssessmentResult(
            assessment_id=assessment_id,
            student_id=item.student_id,
            marks_obtained=item.marks_obtained,
            percentage=pct,
            grade=grade,
            is_absent=item.is_absent,
            teacher_feedback=item.teacher_feedback,
        )
        db.add(result_obj)
        saved.append(item.student_id)

    await db.flush()
    return {"graded_students": len(saved), "assessment_id": assessment_id}


@router.get("/{assessment_id}/analytics")
async def get_assessment_analytics(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for an assessment (averages, pass rate, distribution)."""
    from sqlalchemy import func, and_
    result = await db.execute(
        select(
            func.count(AssessmentResult.id).label("total"),
            func.avg(AssessmentResult.percentage).label("avg_pct"),
            func.min(AssessmentResult.percentage).label("min_pct"),
            func.max(AssessmentResult.percentage).label("max_pct"),
            func.sum(
                (AssessmentResult.percentage >= 35).cast(int)
            ).label("pass_count"),
        ).where(
            and_(
                AssessmentResult.assessment_id == assessment_id,
                AssessmentResult.is_absent == False,
            )
        )
    )
    row = result.one()
    return {
        "assessment_id": assessment_id,
        "total_students": row.total,
        "average_percentage": round(row.avg_pct or 0, 2),
        "min_percentage": round(row.min_pct or 0, 2),
        "max_percentage": round(row.max_pct or 0, 2),
        "pass_rate": round((row.pass_count / row.total * 100) if row.total else 0, 2),
    }
