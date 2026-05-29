from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_teacher, require_hm
from app.models.user import User
from app.schemas.student import (
    StudentCreateRequest, StudentUpdateRequest,
    StudentResponse, StudentFilterRequest,
)
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentResponse, status_code=201)
async def create_student(
    request: StudentCreateRequest,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Create a new student record."""
    service = StudentService(db)
    return await service.create_student(request)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get student details by ID."""
    service = StudentService(db)
    return await service.get_student(student_id)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    request: StudentUpdateRequest,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Update student information."""
    service = StudentService(db)
    return await service.update_student(student_id, request)


@router.get("/")
async def list_students(
    school_id: int | None = Query(None),
    class_grade: int | None = Query(None),
    section: str | None = Query(None),
    risk_level: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List students with filtering and pagination."""
    service = StudentService(db)
    filters = StudentFilterRequest(
        school_id=school_id,
        class_grade=class_grade,
        section=section,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
    )
    return await service.list_students(filters)


@router.get("/school/{school_id}/high-risk")
async def get_high_risk_students(
    school_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Get all high-risk and critical-risk students in a school."""
    service = StudentService(db)
    return await service.get_high_risk_students(school_id)


@router.post("/{student_id}/dropout")
async def mark_dropout(
    student_id: int,
    reason: str = Query(...),
    dropout_date: str = Query(...),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Mark a student as dropped out."""
    service = StudentService(db)
    return await service.mark_dropout(student_id, reason, dropout_date)
