"""
Attendance service — mark, bulk-mark, and summarise attendance.
Shares the same DB session as EduSakhi, so attendance records reference the
same `students` table used by the learning engine.
"""

from typing import List

from sqlalchemy.orm import Session

from database.models import Attendance
from governance.schemas import AttendanceMark, AttendanceBulkMark

VALID_STATUSES = {"present", "absent", "late"}


def _normalise_status(status: str) -> str:
    s = (status or "present").lower().strip()
    return s if s in VALID_STATUSES else "present"


def mark_attendance(data: AttendanceMark, marked_by: int, db: Session) -> Attendance:
    """Mark (or update) one student's attendance for a date."""
    record = (
        db.query(Attendance)
        .filter(
            Attendance.student_id == data.student_id,
            Attendance.date == data.date,
        )
        .first()
    )
    status = _normalise_status(data.status)

    if record:
        record.status = status
        record.marked_by = marked_by
        record.school_id = data.school_id
    else:
        record = Attendance(
            student_id=data.student_id,
            school_id=data.school_id,
            date=data.date,
            status=status,
            marked_by=marked_by,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def bulk_mark_attendance(
    data: AttendanceBulkMark, marked_by: int, db: Session
) -> List[Attendance]:
    """Mark attendance for many students at once (one class/school, one date)."""
    saved: List[Attendance] = []
    for entry in data.records:
        saved.append(
            mark_attendance(
                AttendanceMark(
                    student_id=entry.student_id,
                    school_id=data.school_id,
                    date=data.date,
                    status=entry.status,
                ),
                marked_by=marked_by,
                db=db,
            )
        )
    return saved


def get_student_summary(student_id: int, db: Session) -> dict:
    """Compute an attendance summary for one student."""
    records = (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id)
        .all()
    )
    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    late = sum(1 for r in records if r.status == "late")
    pct = round((present + late) / total * 100, 2) if total else 0.0

    return {
        "student_id": student_id,
        "total_days": total,
        "present": present,
        "absent": absent,
        "late": late,
        "attendance_percentage": pct,
    }
