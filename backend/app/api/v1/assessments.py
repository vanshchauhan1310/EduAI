from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
import json

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResult, AssessmentType
from app.models.teacher import Teacher
from app.models.student import Student
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])


async def _get_or_create_teacher_profile(current_user: User, db: AsyncSession) -> Teacher | None:
    """Resolve the Teacher row for the logged-in user, auto-provisioning one if missing.

    Some teacher accounts (e.g. self-registered) have no `teachers` row yet. Without
    this, assessment creation and the "my assessments" listing resolved the teacher
    independently and could disagree (one falling back to a hardcoded id, the other
    returning empty), so created assessments would silently vanish from the list.
    """
    result = await db.execute(select(Teacher).where(Teacher.user_id == current_user.id))
    teacher = result.scalar_one_or_none()
    if teacher or not current_user.school_id:
        return teacher

    teacher = Teacher(
        employee_id=f"AUTO-{current_user.id}",
        user_id=current_user.id,
        school_id=current_user.school_id,
    )
    db.add(teacher)
    await db.flush()
    await db.refresh(teacher)
    return teacher


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


class AIQuestionGenerateRequest(BaseModel):
    chapter_id: str
    subject: str
    class_grade: int
    difficulty: str = "MEDIUM"  # EASY, MEDIUM, HARD
    num_questions: int = 5


class StudentAnswerSubmit(BaseModel):
    question_id: str
    answer_text: str


class AssessmentQuestionsResponse(BaseModel):
    assessment_id: int
    questions: list[dict]
    total_questions: int
    total_marks: int


class StudentSubmissionResponse(BaseModel):
    id: int
    assessment_id: int
    student_id: int
    score: float | None
    max_score: float
    percentage: float | None
    feedback: str | None
    submitted_at: str
    graded_at: str | None


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
    teacher = await _get_or_create_teacher_profile(current_user, db)
    if not teacher:
        raise HTTPException(
            status_code=400,
            detail="Your account has no school assigned, so an assessment cannot be created. Contact your administrator."
        )

    assessment = Assessment(
        title=request.title,
        assessment_type=request.assessment_type,
        subject=request.subject,
        class_grade=request.class_grade,
        section=request.section,
        school_id=request.school_id,
        teacher_id=teacher.id,
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


@router.get("/my")
async def list_my_assessments(
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """List all assessments created by the current teacher (generated and/or published)."""
    teacher = await _get_or_create_teacher_profile(current_user, db)
    if not teacher:
        return []

    result = await db.execute(
        select(Assessment)
        .where(Assessment.teacher_id == teacher.id)
        .order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()
    if not assessments:
        return []

    assessment_ids = [a.id for a in assessments]
    counts_result = await db.execute(
        select(AssessmentResult.assessment_id, func.count(AssessmentResult.id))
        .where(AssessmentResult.assessment_id.in_(assessment_ids))
        .group_by(AssessmentResult.assessment_id)
    )
    submissions_by_assessment = dict(counts_result.all())

    return [
        {
            "id": a.id,
            "title": a.title,
            "type": a.assessment_type.value,
            "subject": a.subject,
            "class_grade": a.class_grade,
            "section": a.section,
            "max_marks": a.max_marks,
            "is_published": a.is_published,
            "has_questions": bool(a.questions_json),
            "submissions_count": submissions_by_assessment.get(a.id, 0),
            "created_at": a.created_at.isoformat(),
        }
        for a in assessments
    ]


@router.get("/student/my")
async def list_my_student_assessments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List published assessments visible to the current student, with attempt status,
    and — for attempted ones — the marks, teacher feedback and AI insights."""
    student_result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    assessments_result = await db.execute(
        select(Assessment)
        .where(
            Assessment.is_published == True,  # noqa: E712
            Assessment.school_id == student.school_id,
            Assessment.class_grade == student.current_class,
        )
        .order_by(Assessment.created_at.desc())
    )
    assessments = [
        a for a in assessments_result.scalars().all()
        if not a.section or not student.section or a.section == student.section
    ]
    if not assessments:
        return []

    assessment_ids = [a.id for a in assessments]
    results_result = await db.execute(
        select(AssessmentResult).where(
            AssessmentResult.assessment_id.in_(assessment_ids),
            AssessmentResult.student_id == student.id,
        )
    )
    result_by_assessment = {r.assessment_id: r for r in results_result.scalars().all()}

    response = []
    for a in assessments:
        submission = result_by_assessment.get(a.id)
        item = {
            "id": a.id,
            "title": a.title,
            "type": a.assessment_type.value,
            "subject": a.subject,
            "max_marks": a.max_marks,
            "duration_minutes": a.duration_minutes,
            "scheduled_date": a.scheduled_date.isoformat() if a.scheduled_date else None,
            "attempted": submission is not None,
            "is_graded": bool(submission and submission.marks_obtained is not None),
        }
        if submission:
            ai_insights = None
            if submission.remarks:
                try:
                    ai_insights = json.loads(submission.remarks).get("ai_evaluation")
                except (ValueError, AttributeError):
                    ai_insights = None
            item.update({
                "marks_obtained": submission.marks_obtained,
                "percentage": submission.percentage,
                "grade": submission.grade,
                "feedback": submission.teacher_feedback,
                "ai_insights": ai_insights,
                "submitted_at": submission.created_at.isoformat(),
            })
        response.append(item)

    return response


@router.post("/{assessment_id}/publish")
async def publish_assessment(
    assessment_id: int,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Publish an assessment so it becomes visible/available to students."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.questions_json:
        raise HTTPException(
            status_code=400,
            detail="Generate questions for this assessment before publishing it"
        )

    assessment.is_published = True
    await db.flush()
    return {"id": assessment.id, "title": assessment.title, "is_published": assessment.is_published}


@router.get("/{assessment_id}/submissions")
async def list_assessment_submissions(
    assessment_id: int,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """List students who attempted this assessment, with their (AI-)graded results."""
    assessment_result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = assessment_result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await db.execute(
        select(AssessmentResult, Student)
        .join(Student, AssessmentResult.student_id == Student.id)
        .where(AssessmentResult.assessment_id == assessment_id)
        .order_by(AssessmentResult.created_at.asc())
    )
    rows = result.all()

    return {
        "assessment_id": assessment_id,
        "assessment_title": assessment.title,
        "max_marks": assessment.max_marks,
        "submissions": [
            {
                "id": submission.id,
                "student_id": submission.student_id,
                "student_name": f"{student.first_name} {student.last_name}",
                "marks_obtained": submission.marks_obtained,
                "percentage": submission.percentage,
                "grade": submission.grade,
                "is_absent": submission.is_absent,
                "is_graded": submission.marks_obtained is not None,
                "feedback": submission.teacher_feedback,
                "submitted_at": submission.created_at.isoformat(),
            }
            for submission, student in rows
        ],
    }


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


# ────────────── AI ASSESSMENT FEATURES ──────────────────────


@router.post("/{assessment_id}/generate-questions")
async def generate_ai_questions(
    assessment_id: int,
    request: AIQuestionGenerateRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI questions for an assessment using LLM.
    Integrates with the existing exam_prep question generation pipeline.
    """
    assessment_lookup = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = assessment_lookup.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    try:
        service = AssessmentService()
        assessment_data = service.generate_assessment(
            chapter_id=request.chapter_id,
            difficulty=request.difficulty,
            num_questions=request.num_questions
        )
        # Persist generated questions on the assessment's own integer id —
        # keeps grading lookups in sync instead of relying on the separate
        # UUID-keyed AssessmentStore file cache.
        assessment.questions_json = json.dumps(assessment_data["questions"])
        await db.flush()

        return {
            "assessment_id": assessment_id,
            "questions_generated": len(assessment_data["questions"]),
            "total_marks": assessment_data["total_marks"],
            "questions": assessment_data["questions"]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.get("/{assessment_id}/questions", response_model=AssessmentQuestionsResponse)
async def get_assessment_questions(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the AI-generated questions for an assessment.
    The answer key (sample_answer / expected_points) is withheld here —
    it's only used internally during AI grading.
    """
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.questions_json:
        return {
            "assessment_id": assessment_id,
            "questions": [],
            "total_questions": 0,
            "total_marks": 0,
        }

    questions = json.loads(assessment.questions_json)
    return {
        "assessment_id": assessment_id,
        "questions": [
            {
                "question_id": q["question_id"],
                "question_text": q["question_text"],
                "marks": q["marks"],
                "pattern": q.get("pattern"),
                "difficulty": q.get("difficulty"),
            }
            for q in questions
        ],
        "total_questions": len(questions),
        "total_marks": sum(q["marks"] for q in questions),
    }


@router.post("/{assessment_id}/student-submission")
async def submit_student_assessment(
    assessment_id: int,
    request: list[StudentAnswerSubmit],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Student submits their assessment answers.
    Stores submission in database for teacher grading.
    """
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get student ID from user
    student_result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can submit assessments")
    student_id = student.id

    # Check if student already submitted
    existing = await db.execute(
        select(AssessmentResult).where(
            and_(
                AssessmentResult.assessment_id == assessment_id,
                AssessmentResult.student_id == student_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already submitted this assessment")

    # Create submission record (in production, store answer details)
    submission = AssessmentResult(
        assessment_id=assessment_id,
        student_id=student_id,
        is_absent=False,
        remarks=json.dumps({"answers": [a.dict() for a in request]})
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    return {
        "submission_id": submission.id,
        "status": "SUBMITTED",
        "message": "Assessment submitted successfully. Awaiting teacher grading."
    }


@router.post("/{assessment_id}/ai-grade")
async def grade_student_submission(
    assessment_id: int,
    student_id: int = Body(..., embed=True),
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-assisted grading: evaluates student answers against the rubric using
    semantic similarity + the LLM-generated answer key, and saves the result.
    """
    assessment_result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = assessment_result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.questions_json:
        raise HTTPException(status_code=400, detail="No AI-generated questions found for this assessment")

    result = await db.execute(
        select(AssessmentResult).where(
            and_(
                AssessmentResult.assessment_id == assessment_id,
                AssessmentResult.student_id == student_id
            )
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    try:
        service = AssessmentService()
        questions = json.loads(assessment.questions_json)
        answers = json.loads(submission.remarks or "{}")
        # Evaluate directly against this assessment's own stored questions —
        # avoids the broken UUID lookup that AssessmentStore-based
        # submit_assessment() performed against the integer assessment_id.
        evaluation = service.evaluate_answers(
            questions=questions,
            answers=answers.get("answers", [])
        )

        # Update submission with grades
        submission.marks_obtained = evaluation["total_score"]
        submission.percentage = evaluation["percentage"]
        submission.grade = calculate_grade(evaluation["percentage"])
        submission.teacher_feedback = f"AI Grading Complete. Score: {evaluation['total_score']}/{evaluation['max_score']}"

        # Persist the per-question AI evaluation alongside the stored answers so the
        # student can later see *why* they received their score (matched/missing
        # rubric points, semantic similarity, per-question feedback) — not just the total.
        submission_payload = json.loads(submission.remarks or "{}")
        submission_payload["ai_evaluation"] = evaluation["results"]
        submission.remarks = json.dumps(submission_payload)

        await db.flush()
        return {
            "student_id": student_id,
            "score": submission.marks_obtained,
            "percentage": submission.percentage,
            "grade": submission.grade,
            "feedback": submission.teacher_feedback,
            "detailed_results": evaluation["results"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")
