"""
Risk Detector — detects anomalies across school, mandal, district levels.
Identifies: attendance drops, teacher shortages, performance declines.
"""
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.school import School
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.student import Student, RiskLevel


class RiskDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_school_anomalies(self, school_id: int) -> list[dict]:
        alerts = []
        today = date.today()

        # Attendance drop detection (compare last 7 days vs prior 7 days)
        recent_att = await self._get_attendance_rate(school_id, today - timedelta(7), today)
        prior_att = await self._get_attendance_rate(
            school_id, today - timedelta(14), today - timedelta(7)
        )
        if prior_att > 0 and (prior_att - recent_att) > 0.10:
            alerts.append({
                "type": "ATTENDANCE_DROP",
                "severity": "HIGH",
                "message": f"Attendance dropped {(prior_att - recent_att):.0%} vs previous week",
                "current_rate": f"{recent_att:.0%}",
                "prior_rate": f"{prior_att:.0%}",
                "recommended_action": "Principal investigation required",
            })

        # High-risk student count
        high_risk_count = (await self.db.execute(
            select(func.count(Student.id)).where(
                Student.school_id == school_id,
                Student.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
                Student.is_active == True,
            )
        )).scalar_one()

        total_students = (await self.db.execute(
            select(func.count(Student.id)).where(
                Student.school_id == school_id, Student.is_active == True
            )
        )).scalar_one() or 1

        risk_pct = high_risk_count / total_students
        if risk_pct > 0.15:
            alerts.append({
                "type": "HIGH_DROPOUT_RISK",
                "severity": "CRITICAL",
                "message": f"{risk_pct:.0%} of students are at high/critical dropout risk",
                "affected_count": high_risk_count,
                "recommended_action": "Immediate DEO escalation and counselor deployment",
            })

        return alerts

    async def detect_district_anomalies(self, district_id: int) -> list[dict]:
        alerts = []
        schools_result = await self.db.execute(
            select(School).where(School.district_id == district_id, School.is_active == True)
        )
        schools = list(schools_result.scalars().all())

        low_performing_schools = []
        for school in schools:
            score = school.health_score
            if score is not None and score < 40:
                low_performing_schools.append({
                    "school_id": school.id,
                    "name": school.name,
                    "health_score": score,
                })

        if low_performing_schools:
            alerts.append({
                "type": "LOW_HEALTH_SCHOOLS",
                "severity": "HIGH",
                "message": f"{len(low_performing_schools)} schools have health score below 40",
                "schools": low_performing_schools,
                "recommended_action": "Schedule MEO inspection visits",
            })

        return alerts

    async def _get_attendance_rate(self, school_id: int, from_date: date, to_date: date) -> float:
        result = await self.db.execute(
            select(
                func.count(Attendance.id).label("total"),
                func.sum((Attendance.status == AttendanceStatus.PRESENT).cast(int)).label("present"),
            ).where(
                and_(
                    Attendance.school_id == school_id,
                    Attendance.date >= from_date,
                    Attendance.date <= to_date,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                )
            )
        )
        row = result.one()
        return (row.present / row.total) if row.total else 0.0
