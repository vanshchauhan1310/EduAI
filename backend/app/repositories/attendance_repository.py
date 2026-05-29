from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType


class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, attendance_id: int) -> Attendance | None:
        result = await self.db.execute(select(Attendance).where(Attendance.id == attendance_id))
        return result.scalar_one_or_none()

    async def get_for_student_date(self, student_id: int, attendance_date: date) -> Attendance | None:
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.reference_id == student_id,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                    Attendance.date == attendance_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_student_records(
        self, student_id: int, from_date: date, to_date: date
    ) -> list[Attendance]:
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.reference_id == student_id,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                    Attendance.date >= from_date,
                    Attendance.date <= to_date,
                )
            ).order_by(Attendance.date.desc())
        )
        return list(result.scalars().all())

    async def get_class_attendance(
        self, school_id: int, class_id: int, section: str | None, attendance_date: date
    ) -> list[Attendance]:
        query = select(Attendance).where(
            and_(
                Attendance.school_id == school_id,
                Attendance.class_id == class_id,
                Attendance.date == attendance_date,
                Attendance.reference_type == AttendanceReferenceType.STUDENT,
            )
        )
        if section:
            query = query.where(Attendance.section == section)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_school_attendance_summary(
        self, school_id: int, attendance_date: date
    ) -> dict:
        result = await self.db.execute(
            select(
                Attendance.status,
                func.count(Attendance.id).label("count"),
            ).where(
                and_(
                    Attendance.school_id == school_id,
                    Attendance.date == attendance_date,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                )
            ).group_by(Attendance.status)
        )
        rows = result.all()
        summary = {row.status: row.count for row in rows}
        total = sum(summary.values())
        present = summary.get(AttendanceStatus.PRESENT, 0) + summary.get(AttendanceStatus.LATE, 0)
        return {
            "total": total,
            "present": present,
            "absent": summary.get(AttendanceStatus.ABSENT, 0),
            "late": summary.get(AttendanceStatus.LATE, 0),
            "rate": round((present / total * 100) if total > 0 else 0, 2),
        }

    async def create(self, record: Attendance) -> Attendance:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def bulk_create(self, records: list[Attendance]) -> list[Attendance]:
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def update(self, record: Attendance) -> Attendance:
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_consecutive_absences(self, student_id: int, as_of: date) -> int:
        records = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.reference_id == student_id,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                    Attendance.date <= as_of,
                )
            ).order_by(Attendance.date.desc()).limit(30)
        )
        records_list = list(records.scalars().all())
        count = 0
        for r in records_list:
            if r.status == AttendanceStatus.ABSENT:
                count += 1
            else:
                break
        return count
