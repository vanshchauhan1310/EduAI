"""
Attendance routes — mark, bulk-mark, summary.
Staff roles (teacher/HM/officers) mark; anyone authenticated can read a summary.
Mounted under /api/v1/attendance.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import require_roles, get_current_user
from core.roles import Role
from database.db import get_db
from database.models import User
from governance import attendance_service
from governance.schemas import (
    AttendanceMark, AttendanceBulkMark, AttendanceOut, AttendanceSummary,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

_STAFF = (Role.TEACHER, Role.HM, Role.DEO, Role.MEO, Role.BEO)


@router.post("/mark", response_model=AttendanceOut)
def mark(
    data: AttendanceMark,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_STAFF)),
):
    """Mark a single student's attendance."""
    return attendance_service.mark_attendance(data, marked_by=current_user.id, db=db)


@router.post("/bulk-mark", response_model=List[AttendanceOut])
def bulk_mark(
    data: AttendanceBulkMark,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_STAFF)),
):
    """Mark attendance for a whole class at once."""
    return attendance_service.bulk_mark_attendance(
        data, marked_by=current_user.id, db=db
    )


@router.get("/summary/{student_id}", response_model=AttendanceSummary)
def summary(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attendance summary for one student."""
    return attendance_service.get_student_summary(student_id, db)
