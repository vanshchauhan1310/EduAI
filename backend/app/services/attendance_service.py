from datetime import date, datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.user import User
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.attendance import (
    AttendanceMarkRequest, BulkAttendanceRequest,
    AttendanceSummary, AttendanceResponse,
)


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AttendanceRepository(db)

    async def mark_attendance(self, request: AttendanceMarkRequest, marked_by: User) -> AttendanceResponse:
        # Prevent duplicate marking
        if request.reference_type == AttendanceReferenceType.STUDENT:
            existing = await self.repo.get_for_student_date(request.reference_id, request.date)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Attendance already marked for student {request.reference_id} on {request.date}",
                )

        is_geo_verified = False
        if request.latitude and request.longitude:
            is_geo_verified = True

        record = Attendance(
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            school_id=request.school_id,
            date=request.date,
            status=request.status,
            session=request.session,
            class_id=request.class_id,
            section=request.section,
            latitude=request.latitude,
            longitude=request.longitude,
            is_geo_verified=is_geo_verified,
            marked_by_id=marked_by.id,
            remarks=request.remarks,
        )
        saved = await self.repo.create(record)
        return AttendanceResponse.model_validate(saved)

    async def bulk_mark_attendance(self, request: BulkAttendanceRequest, marked_by: User) -> dict:
        records = []
        skipped = []

        for item in request.records:
            if request.reference_type == AttendanceReferenceType.STUDENT:
                existing = await self.repo.get_for_student_date(item.reference_id, request.date)
                if existing:
                    skipped.append(item.reference_id)
                    continue

            record = Attendance(
                reference_type=request.reference_type,
                reference_id=item.reference_id,
                school_id=request.school_id,
                date=request.date,
                status=item.status,
                session=request.session,
                class_id=request.class_id,
                section=request.section,
                latitude=request.latitude,
                longitude=request.longitude,
                is_geo_verified=bool(request.latitude and request.longitude),
                marked_by_id=marked_by.id,
                remarks=item.remarks,
            )
            records.append(record)

        saved = await self.repo.bulk_create(records)
        return {
            "marked": len(saved),
            "skipped": len(skipped),
            "skipped_ids": skipped,
        }

    async def get_student_summary(self, student_id: int, from_date: date, to_date: date) -> AttendanceSummary:
        records = await self.repo.get_student_records(student_id, from_date, to_date)

        total = len(records)
        present = sum(1 for r in records if r.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE))
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        half_day = sum(1 for r in records if r.status == AttendanceStatus.HALF_DAY)
        pct = round((present / total * 100) if total > 0 else 0, 2)

        consecutive = await self.repo.get_consecutive_absences(student_id, to_date)
        last_absent = next((r.date for r in records if r.status == AttendanceStatus.ABSENT), None)

        return AttendanceSummary(
            total_days=total,
            present_days=present,
            absent_days=absent,
            late_days=late,
            half_days=half_day,
            attendance_percentage=pct,
            consecutive_absences=consecutive,
            last_absent_date=last_absent,
        )

    async def get_school_daily_summary(self, school_id: int, summary_date: date) -> dict:
        return await self.repo.get_school_attendance_summary(school_id, summary_date)
