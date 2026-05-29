from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.schemas.attendance import (
    AttendanceMarkRequest, BulkAttendanceRequest,
    AttendanceSummary, AttendanceAnalyticsRequest,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/mark")
async def mark_attendance(
    request: AttendanceMarkRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for a single student or teacher."""
    service = AttendanceService(db)
    return await service.mark_attendance(request, current_user)


@router.post("/mark/bulk")
async def bulk_mark_attendance(
    request: BulkAttendanceRequest,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for an entire class at once."""
    service = AttendanceService(db)
    return await service.bulk_mark_attendance(request, current_user)


@router.get("/student/{student_id}/summary", response_model=AttendanceSummary)
async def get_student_attendance_summary(
    student_id: int,
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance summary for a specific student over a date range."""
    service = AttendanceService(db)
    return await service.get_student_summary(student_id, from_date, to_date)


@router.get("/school/{school_id}/daily")
async def get_school_daily_attendance(
    school_id: int,
    report_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get school-wide attendance summary for a given date."""
    service = AttendanceService(db)
    return await service.get_school_daily_summary(school_id, report_date)


@router.get("/student/{student_id}/records")
async def get_student_attendance_records(
    student_id: int,
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get raw attendance records for a student."""
    from app.repositories.attendance_repository import AttendanceRepository
    repo = AttendanceRepository(db)
    records = await repo.get_student_records(student_id, from_date, to_date)
    return [
        {
            "id": r.id,
            "date": str(r.date),
            "status": r.status.value,
            "session": r.session,
            "remarks": r.remarks,
        }
        for r in records
    ]
