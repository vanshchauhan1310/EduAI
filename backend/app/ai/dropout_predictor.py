"""
Dropout Prediction Engine
Uses a rule-based scoring model (Phase 1) with hooks for ML model inference (Phase 3).
Features: attendance rate, consecutive absences, assessment performance, risk flags.
"""
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.student import Student, RiskLevel
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.assessment import AssessmentResult
from app.models.ai_insight import AIInsight, InsightType, InsightScope


WEIGHTS = {
    "attendance_rate": 0.35,
    "consecutive_absences": 0.25,
    "assessment_performance": 0.20,
    "socio_economic": 0.10,
    "gender_distance": 0.05,
    "disability": 0.05,
}


def _score_to_risk_level(score: float) -> RiskLevel:
    if score >= 0.80: return RiskLevel.CRITICAL
    if score >= 0.65: return RiskLevel.HIGH
    if score >= 0.40: return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _score_to_label(score: float) -> str:
    if score >= 0.80: return "CRITICAL"
    if score >= 0.65: return "HIGH"
    if score >= 0.40: return "MEDIUM"
    return "LOW"


class DropoutPredictor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_attendance_features(self, student_id: int) -> dict:
        to_date = date.today()
        from_date = to_date - timedelta(days=90)

        result = await self.db.execute(
            select(
                Attendance.status,
                func.count(Attendance.id).label("count"),
            ).where(
                and_(
                    Attendance.reference_id == student_id,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                    Attendance.date >= from_date,
                    Attendance.date <= to_date,
                )
            ).group_by(Attendance.status)
        )
        rows = result.all()
        totals = {r.status: r.count for r in rows}
        total = sum(totals.values())
        present = totals.get(AttendanceStatus.PRESENT, 0) + totals.get(AttendanceStatus.LATE, 0)
        attendance_rate = (present / total) if total > 0 else 1.0

        # Consecutive absences
        records_result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.reference_id == student_id,
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                )
            ).order_by(Attendance.date.desc()).limit(30)
        )
        records = list(records_result.scalars().all())
        consecutive = 0
        for r in records:
            if r.status == AttendanceStatus.ABSENT:
                consecutive += 1
            else:
                break

        return {
            "attendance_rate": attendance_rate,
            "consecutive_absences": consecutive,
            "total_days_recorded": total,
        }

    async def _get_assessment_features(self, student_id: int) -> dict:
        result = await self.db.execute(
            select(func.avg(AssessmentResult.percentage)).where(
                and_(
                    AssessmentResult.student_id == student_id,
                    AssessmentResult.is_absent == False,
                    AssessmentResult.percentage.isnot(None),
                )
            )
        )
        avg_pct = result.scalar_one_or_none() or 0.0
        return {"avg_assessment_pct": avg_pct}

    async def predict(self, student_id: int) -> dict:
        student_result = await self.db.execute(select(Student).where(Student.id == student_id))
        student = student_result.scalar_one_or_none()
        if not student:
            return {"error": "Student not found"}

        att_features = await self._get_attendance_features(student_id)
        assess_features = await self._get_assessment_features(student_id)

        # Score components (0.0 = low risk, 1.0 = high risk)
        att_rate = att_features["attendance_rate"]
        att_risk = max(0.0, 1.0 - att_rate)  # lower attendance → higher risk

        consec = att_features["consecutive_absences"]
        consec_risk = min(1.0, consec / 10.0)  # 10+ consecutive = max risk

        avg_pct = assess_features["avg_assessment_pct"]
        assess_risk = max(0.0, 1.0 - (avg_pct / 100.0)) if avg_pct else 0.5

        socio_risk = 0.3 if student.receives_scholarship else 0.0
        gender_risk = 0.2 if (student.gender.value == "FEMALE" and student.current_class >= 6) else 0.0
        disability_risk = 0.4 if student.has_disability else 0.0

        risk_score = (
            att_risk * WEIGHTS["attendance_rate"]
            + consec_risk * WEIGHTS["consecutive_absences"]
            + assess_risk * WEIGHTS["assessment_performance"]
            + socio_risk * WEIGHTS["socio_economic"]
            + gender_risk * WEIGHTS["gender_distance"]
            + disability_risk * WEIGHTS["disability"]
        )
        risk_score = round(min(1.0, max(0.0, risk_score)), 4)
        risk_level = _score_to_risk_level(risk_score)

        risk_factors = []
        if att_rate < 0.75:
            risk_factors.append(f"Low attendance rate: {att_rate:.0%}")
        if consec > 3:
            risk_factors.append(f"Consecutive absences: {consec} days")
        if avg_pct and avg_pct < 40:
            risk_factors.append(f"Below-average performance: {avg_pct:.1f}%")
        if student.has_disability:
            risk_factors.append("Has documented disability")

        recommendations = []
        if risk_score >= 0.65:
            recommendations.append("Schedule immediate counselor visit")
            recommendations.append("Notify parent/guardian via WhatsApp")
        if att_rate < 0.75:
            recommendations.append("Issue attendance warning notice")
        if avg_pct and avg_pct < 40:
            recommendations.append("Assign remedial classes in weak subjects")

        # Persist the insight
        insight = AIInsight(
            insight_type=InsightType.DROPOUT_RISK,
            scope=InsightScope.STUDENT,
            reference_id=student_id,
            risk_score=risk_score,
            confidence=0.78,
            summary=f"{student.full_name} has a {_score_to_label(risk_score)} dropout risk ({risk_score:.0%}).",
            detailed_analysis=f"Attendance: {att_rate:.0%}, Consecutive absences: {consec}, Avg marks: {avg_pct:.1f}%",
            recommendations=str(recommendations),
            model_version="rule-based-v1.0",
            feature_values={
                "attendance_rate": att_rate,
                "consecutive_absences": consec,
                "avg_assessment_pct": avg_pct,
            },
        )
        self.db.add(insight)

        # Update student risk fields
        student.dropout_risk_score = risk_score
        student.risk_level = risk_level

        await self.db.flush()

        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "features": {
                "attendance_rate": att_rate,
                "consecutive_absences": consec,
                "avg_assessment_percentage": avg_pct,
            },
        }
