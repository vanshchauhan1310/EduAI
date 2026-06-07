"""
Dropout Prediction Repository — Data access layer for student_ml_input and student_predictions tables.

All queries that need student name/admission_no JOIN with the students table.
School/mandal/district analytics JOIN through students → schools → mandals → districts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import (
    and_,
    case,
    func,
    select,
    text,
    update,
    delete,
    desc,
    Integer,
    Float,
    String,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import expression

from app.models.student import Student
from app.models.school import School, Mandal, District
from app.models.student_ml_input import StudentMLInput
from app.models.student_prediction import StudentPrediction

logger = logging.getLogger(__name__)


class DropoutPredictionRepository:
    """Data access for ML input features and prediction outputs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # StudentMLInput — Model Input Features
    # ═══════════════════════════════════════════════════════════

    async def upsert_ml_input(self, input_data: dict[str, Any]) -> StudentMLInput:
        """
        Insert or update ML input features for a student.
        Uses ON CONFLICT (student_id) to upsert.
        """
        stmt = (
            select(StudentMLInput)
            .where(StudentMLInput.student_id == input_data["student_id"])
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in input_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            record = existing
        else:
            record = StudentMLInput(**input_data)
            self.db.add(record)

        await self.db.flush()
        logger.debug("Upserted ML input for student_id=%s", input_data["student_id"])
        return record

    async def bulk_upsert_ml_input(self, inputs: list[dict[str, Any]]) -> int:
        """
        Bulk upsert ML input features for multiple students.
        For each student: insert if not exists, otherwise update.
        """
        count = 0
        for inp in inputs:
            await self.upsert_ml_input(inp)
            count += 1
        await self.db.flush()
        logger.info("Bulk upserted %d ML input records", count)
        return count

    async def get_ml_input(self, student_id: int) -> dict[str, Any] | None:
        """Get ML input features for a student."""
        result = await self.db.execute(
            select(StudentMLInput).where(StudentMLInput.student_id == student_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return {
            "student_id": record.student_id,
            "gender": record.gender,
            "class_level": record.class_level,
            "age": record.age,
            "attendance_pct": record.attendance_pct,
            "avg_marks": record.avg_marks,
            "previous_failures": record.previous_failures,
            "family_income_monthly": record.family_income_monthly,
            "distance_to_school_km": record.distance_to_school_km,
            "guardian_education": record.guardian_education,
            "single_parent": record.single_parent,
            "sibling_dropout": record.sibling_dropout,
            "mobile_available": record.mobile_available,
            "internet_access": record.internet_access,
            "scholarship": record.scholarship,
            "midday_meal": record.midday_meal,
            "study_hours_per_day": record.study_hours_per_day,
            "health_risk": record.health_risk,
            "school_engagement_score": record.school_engagement_score,
            "teacher_feedback_score": record.teacher_feedback_score,
            "disciplinary_incidents": record.disciplinary_incidents,
        }

    # ═══════════════════════════════════════════════════════════
    # StudentPrediction — Model Output
    # ═══════════════════════════════════════════════════════════

    async def create_prediction(
        self, data: dict[str, Any]
    ) -> StudentPrediction:
        """Create a single prediction record."""
        record = StudentPrediction(**data)
        self.db.add(record)
        await self.db.flush()
        return record

    async def bulk_create_predictions(
        self, predictions: list[StudentPrediction]
    ) -> int:
        """Bulk insert prediction records."""
        for pred in predictions:
            self.db.add(pred)
        await self.db.flush()
        logger.info("Bulk created %d prediction records", len(predictions))
        return len(predictions)

    async def get_latest_prediction_by_student(
        self, student_id: int
    ) -> dict[str, Any] | None:
        """
        Get the latest prediction for a student, enriched with student name/school info.
        JOINs: student_predictions → students → schools
        """
        stmt = (
            select(
                StudentPrediction.id.label("prediction_id"),
                StudentPrediction.student_id,
                StudentPrediction.dropout_probability,
                StudentPrediction.risk_level,
                StudentPrediction.recommendation,
                StudentPrediction.model_version,
                StudentPrediction.predicted_at,
                StudentPrediction.batch_id,
                Student.id.label("sid"),
                Student.first_name,
                Student.last_name,
                Student.admission_no,
                Student.current_class,
                Student.section,
                Student.academic_year,
                School.id.label("school_id"),
                School.name.label("school_name"),
            )
            .join(Student, StudentPrediction.student_id == Student.id)
            .join(School, Student.school_id == School.id)
            .where(StudentPrediction.student_id == student_id)
            .order_by(desc(StudentPrediction.predicted_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None

        return {
            "prediction_id": row.prediction_id,
            "student_id": row.student_id,
            "student_name": f"{row.first_name} {row.last_name}",
            "admission_no": row.admission_no,
            "school_id": row.school_id,
            "school_name": row.school_name,
            "current_class": row.current_class,
            "section": row.section,
            "academic_year": row.academic_year,
            "dropout_probability": float(row.dropout_probability),
            "risk_level": row.risk_level,
            "recommendation": row.recommendation,
            "predicted_at": row.predicted_at.isoformat() if row.predicted_at else None,
        }

    async def get_high_risk_students(
        self,
        school_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return high-risk and critical-risk students with student name/school info.
        JOINs: student_predictions → students → schools
        """
        conditions = [
            StudentPrediction.risk_level.in_(["High", "Critical"]),
        ]

        if school_id is not None:
            conditions.append(Student.school_id == school_id)

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(StudentPrediction)
            .join(Student, StudentPrediction.student_id == Student.id)
            .where(and_(*conditions))
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get paginated results
        stmt = (
            select(
                StudentPrediction.id.label("prediction_id"),
                StudentPrediction.student_id,
                StudentPrediction.dropout_probability,
                StudentPrediction.risk_level,
                StudentPrediction.recommendation,
                StudentPrediction.predicted_at,
                Student.first_name,
                Student.last_name,
                Student.admission_no,
                Student.current_class,
                Student.school_id,
                School.name.label("school_name"),
            )
            .join(Student, StudentPrediction.student_id == Student.id)
            .join(School, Student.school_id == School.id)
            .where(and_(*conditions))
            .order_by(desc(StudentPrediction.dropout_probability))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = [
            {
                "prediction_id": r.prediction_id,
                "student_id": r.student_id,
                "student_name": f"{r.first_name} {r.last_name}",
                "admission_no": r.admission_no,
                "school_id": r.school_id,
                "school_name": r.school_name,
                "current_class": r.current_class,
                "dropout_probability": float(r.dropout_probability),
                "risk_level": r.risk_level,
                "recommendation": r.recommendation,
                "predicted_at": r.predicted_at.isoformat() if r.predicted_at else None,
            }
            for r in rows
        ]

        return items, total

    # ═══════════════════════════════════════════════════════════
    # School-Level Analytics (MEO Dashboard)
    # ═══════════════════════════════════════════════════════════

    async def get_school_summary(
        self, school_id: int
    ) -> dict[str, Any] | None:
        """Get school-level dropout summary."""
        # Verify school exists
        school_result = await self.db.execute(
            select(School).where(School.id == school_id)
        )
        school = school_result.scalar_one_or_none()
        if school is None:
            return None

        # Aggregate predictions for this school
        agg_stmt = (
            select(
                func.count(StudentPrediction.id).label("total_predictions"),
                func.sum(
                    case(
                        (StudentPrediction.risk_level == "High", 1),
                        else_=0,
                    )
                ).label("high_risk_count"),
                func.sum(
                    case(
                        (StudentPrediction.risk_level == "Critical", 1),
                        else_=0,
                    )
                ).label("critical_risk_count"),
                func.sum(
                    case(
                        (StudentPrediction.risk_level == "Medium", 1),
                        else_=0,
                    )
                ).label("medium_risk_count"),
                func.sum(
                    case(
                        (StudentPrediction.risk_level == "Low", 1),
                        else_=0,
                    )
                ).label("low_risk_count"),
                func.avg(StudentPrediction.dropout_probability).label(
                    "average_risk_score"
                ),
                func.max(StudentPrediction.predicted_at).label("last_prediction_at"),
            )
            .select_from(StudentPrediction)
            .join(Student, StudentPrediction.student_id == Student.id)
            .where(Student.school_id == school_id)
        )
        agg_result = await self.db.execute(agg_stmt)
        agg = agg_result.one_or_none()

        if agg is None or agg.total_predictions == 0:
            return {
                "school_id": school_id,
                "school_name": school.name,
                "total_students": 0,
                "total_predictions": 0,
                "high_risk_count": 0,
                "critical_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "average_risk_score": 0.0,
                "top_risk_factors": [],
                "last_prediction_at": None,
            }

        total_students_result = await self.db.execute(
            select(func.count(Student.id)).where(
                and_(Student.school_id == school_id, Student.is_active == True)
            )
        )
        total_students = total_students_result.scalar() or 0

        # Top risk factors from ML input features (average attendance < 75%)
        low_attendance_stmt = (
            select(func.count(StudentMLInput.student_id))
            .join(Student, StudentMLInput.student_id == Student.id)
            .where(
                and_(
                    Student.school_id == school_id,
                    StudentMLInput.attendance_pct < 75,
                )
            )
        )
        low_att_result = await self.db.execute(low_attendance_stmt)
        low_attendance_count = low_att_result.scalar() or 0

        top_risk_factors = []
        if low_attendance_count > 0:
            top_risk_factors.append(f"Low attendance ({low_attendance_count} students)")

        return {
            "school_id": school_id,
            "school_name": school.name,
            "total_students": total_students,
            "total_predictions": int(agg.total_predictions),
            "high_risk_count": int(agg.high_risk_count or 0),
            "critical_risk_count": int(agg.critical_risk_count or 0),
            "medium_risk_count": int(agg.medium_risk_count or 0),
            "low_risk_count": int(agg.low_risk_count or 0),
            "average_risk_score": round(float(agg.average_risk_score or 0), 2),
            "top_risk_factors": top_risk_factors,
            "last_prediction_at": agg.last_prediction_at.isoformat()
            if agg.last_prediction_at
            else None,
        }

    async def get_school_students(
        self, school_id: int
    ) -> list[dict[str, Any]]:
        """Get all predictions for students in a school, with names."""
        stmt = (
            select(
                StudentPrediction.student_id,
                Student.first_name,
                Student.last_name,
                Student.admission_no,
                Student.current_class,
                StudentPrediction.dropout_probability,
                StudentPrediction.risk_level,
                StudentPrediction.recommendation,
            )
            .join(Student, StudentPrediction.student_id == Student.id)
            .where(Student.school_id == school_id)
            .order_by(desc(StudentPrediction.dropout_probability))
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "student_id": r.student_id,
                "student_name": f"{r.first_name} {r.last_name}",
                "admission_no": r.admission_no,
                "current_class": r.current_class,
                "dropout_probability": float(r.dropout_probability),
                "risk_level": r.risk_level,
                "recommendation": r.recommendation,
            }
            for r in rows
        ]

    # ═══════════════════════════════════════════════════════════
    # Mandal-Level Analytics
    # ═══════════════════════════════════════════════════════════

    async def get_mandal_summary(
        self, mandal_id: int
    ) -> dict[str, Any] | None:
        """Get mandal-level dropout summary aggregated across schools."""
        mandal_result = await self.db.execute(
            select(Mandal, District)
            .join(District, Mandal.district_id == District.id)
            .where(Mandal.id == mandal_id)
        )
        mandal_row = mandal_result.one_or_none()
        if mandal_row is None:
            return None

        mandal, district = mandal_row

        # Get all schools in this mandal
        schools_result = await self.db.execute(
            select(School.id, School.name).where(School.mandal_id == mandal_id)
        )
        schools = schools_result.all()

        school_items = []
        total_students = 0
        total_high_risk = 0
        total_critical_risk = 0
        risk_scores = []

        for school_id, school_name in schools:
            # Active students count
            student_count_result = await self.db.execute(
                select(func.count(Student.id)).where(
                    and_(
                        Student.school_id == school_id,
                        Student.is_active == True,
                    )
                )
            )
            student_count = student_count_result.scalar() or 0
            total_students += student_count

            # Prediction aggregation for this school
            agg_stmt = (
                select(
                    func.sum(
                        case(
                            (StudentPrediction.risk_level == "High", 1),
                            else_=0,
                        )
                    ).label("high_risk_count"),
                    func.sum(
                        case(
                            (StudentPrediction.risk_level == "Critical", 1),
                            else_=0,
                        )
                    ).label("critical_risk_count"),
                    func.avg(StudentPrediction.dropout_probability).label(
                        "avg_risk"
                    ),
                )
                .select_from(StudentPrediction)
                .join(Student, StudentPrediction.student_id == Student.id)
                .where(Student.school_id == school_id)
            )
            agg_result = await self.db.execute(agg_stmt)
            agg = agg_result.one_or_none()

            h_count = int(agg.high_risk_count or 0) if agg else 0
            c_count = int(agg.critical_risk_count or 0) if agg else 0
            avg_risk = float(agg.avg_risk or 0) if agg else 0.0

            total_high_risk += h_count
            total_critical_risk += c_count
            if avg_risk > 0:
                risk_scores.append(avg_risk)

            school_items.append({
                "school_id": school_id,
                "school_name": school_name,
                "total_students": student_count,
                "high_risk_count": h_count,
                "critical_risk_count": c_count,
                "average_risk_score": round(avg_risk, 2),
            })

        overall_avg = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0

        # Last prediction time
        last_pred_result = await self.db.execute(
            select(func.max(StudentPrediction.predicted_at))
            .select_from(StudentPrediction)
            .join(Student, StudentPrediction.student_id == Student.id)
            .join(School, Student.school_id == School.id)
            .where(School.mandal_id == mandal_id)
        )
        last_pred = last_pred_result.scalar()

        return {
            "mandal_id": mandal.id,
            "mandal_name": mandal.name,
            "district_name": district.name,
            "total_schools": len(schools),
            "total_students": total_students,
            "total_high_risk": total_high_risk,
            "total_critical_risk": total_critical_risk,
            "overall_average_risk": overall_avg,
            "schools": school_items,
            "last_prediction_at": last_pred.isoformat() if last_pred else None,
        }

    # ═══════════════════════════════════════════════════════════
    # District-Level Analytics (DEO Dashboard)
    # ═══════════════════════════════════════════════════════════

    async def get_district_summary(
        self, district_id: int
    ) -> dict[str, Any] | None:
        """Get district-level dropout summary aggregated across mandals."""
        district_result = await self.db.execute(
            select(District).where(District.id == district_id)
        )
        district = district_result.scalar_one_or_none()
        if district is None:
            return None

        # Get all mandals in this district
        mandals_result = await self.db.execute(
            select(Mandal.id, Mandal.name).where(Mandal.district_id == district_id)
        )
        mandals = mandals_result.all()

        mandal_items = []
        total_schools = 0
        total_students = 0
        total_high_risk = 0
        total_critical_risk = 0
        risk_scores = []

        for mandal_id, mandal_name in mandals:
            # Schools in this mandal
            schools_result = await self.db.execute(
                select(func.count(School.id)).where(School.mandal_id == mandal_id)
            )
            school_count = schools_result.scalar() or 0
            total_schools += school_count

            # Students in this mandal
            student_count_result = await self.db.execute(
                select(func.count(Student.id))
                .join(School, Student.school_id == School.id)
                .where(
                    and_(
                        School.mandal_id == mandal_id,
                        Student.is_active == True,
                    )
                )
            )
            student_count = student_count_result.scalar() or 0
            total_students += student_count

            # Prediction aggregation
            agg_stmt = (
                select(
                    func.sum(
                        case(
                            (StudentPrediction.risk_level == "High", 1),
                            else_=0,
                        )
                    ).label("high_risk_count"),
                    func.sum(
                        case(
                            (StudentPrediction.risk_level == "Critical", 1),
                            else_=0,
                        )
                    ).label("critical_risk_count"),
                    func.avg(StudentPrediction.dropout_probability).label(
                        "avg_risk"
                    ),
                )
                .select_from(StudentPrediction)
                .join(Student, StudentPrediction.student_id == Student.id)
                .join(School, Student.school_id == School.id)
                .where(School.mandal_id == mandal_id)
            )
            agg_result = await self.db.execute(agg_stmt)
            agg = agg_result.one_or_none()

            h_count = int(agg.high_risk_count or 0) if agg else 0
            c_count = int(agg.critical_risk_count or 0) if agg else 0
            avg_risk = float(agg.avg_risk or 0) if agg else 0.0

            total_high_risk += h_count
            total_critical_risk += c_count
            if avg_risk > 0:
                risk_scores.append(avg_risk)

            mandal_items.append({
                "mandal_id": mandal_id,
                "mandal_name": mandal_name,
                "total_schools": school_count,
                "total_students": student_count,
                "high_risk_count": h_count,
                "critical_risk_count": c_count,
                "average_risk_score": round(avg_risk, 2),
            })

        overall_avg = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0

        # Last prediction time
        last_pred_result = await self.db.execute(
            select(func.max(StudentPrediction.predicted_at))
            .select_from(StudentPrediction)
            .join(Student, StudentPrediction.student_id == Student.id)
            .join(School, Student.school_id == School.id)
            .join(Mandal, School.mandal_id == Mandal.id)
            .where(Mandal.district_id == district_id)
        )
        last_pred = last_pred_result.scalar()

        return {
            "district_id": district.id,
            "district_name": district.name,
            "total_mandals": len(mandals),
            "total_schools": total_schools,
            "total_students": total_students,
            "total_high_risk": total_high_risk,
            "total_critical_risk": total_critical_risk,
            "overall_average_risk": overall_avg,
            "mandals": mandal_items,
            "last_prediction_at": last_pred.isoformat() if last_pred else None,
        }

    # ═══════════════════════════════════════════════════════════
    # Batch Management
    # ═══════════════════════════════════════════════════════════

    async def get_predictions_by_batch(
        self, batch_id: str
    ) -> list[dict[str, Any]]:
        """Get all predictions for a specific batch."""
        stmt = (
            select(
                StudentPrediction.id,
                StudentPrediction.student_id,
                StudentPrediction.dropout_probability,
                StudentPrediction.risk_level,
                StudentPrediction.recommendation,
                StudentPrediction.predicted_at,
                Student.first_name,
                Student.last_name,
                Student.admission_no,
            )
            .join(Student, StudentPrediction.student_id == Student.id)
            .where(StudentPrediction.batch_id == batch_id)
            .order_by(desc(StudentPrediction.dropout_probability))
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": r.id,
                "student_id": r.student_id,
                "student_name": f"{r.first_name} {r.last_name}",
                "admission_no": r.admission_no,
                "dropout_probability": float(r.dropout_probability),
                "risk_level": r.risk_level,
                "recommendation": r.recommendation,
                "predicted_at": r.predicted_at.isoformat() if r.predicted_at else None,
            }
            for r in rows
        ]

    # ═══════════════════════════════════════════════════════════
    # Class-Wise Prediction (HM Dashboard — NEW)
    # ═══════════════════════════════════════════════════════════

    async def get_students_by_class_with_ml_input(
        self,
        school_id: int,
        class_level: int,
    ) -> list[dict[str, Any]]:
        """
        Fetch all active students in a given school+class, joined with their
        ML input features from student_ml_input table.

        Returns a list of dicts with student info + ML features.
        Uses LEFT JOIN to include students even if they don't have ML input yet.
        """
        from sqlalchemy.orm import outerjoin
        stmt = (
            select(
                Student.id.label("student_id"),
                Student.first_name,
                Student.last_name,
                Student.admission_no,
                Student.current_class,
                Student.section,
                Student.gender,
                Student.date_of_birth,
                Student.school_id,
                Student.is_active,
                StudentMLInput.id.label("ml_input_id"),
                StudentMLInput.class_level,
                StudentMLInput.age,
                StudentMLInput.attendance_pct,
                StudentMLInput.avg_marks,
                StudentMLInput.previous_failures,
                StudentMLInput.family_income_monthly,
                StudentMLInput.distance_to_school_km,
                StudentMLInput.guardian_education,
                StudentMLInput.single_parent,
                StudentMLInput.sibling_dropout,
                StudentMLInput.mobile_available,
                StudentMLInput.internet_access,
                StudentMLInput.scholarship,
                StudentMLInput.midday_meal,
                StudentMLInput.study_hours_per_day,
                StudentMLInput.health_risk,
                StudentMLInput.school_engagement_score,
                StudentMLInput.teacher_feedback_score,
                StudentMLInput.disciplinary_incidents,
            )
            .outerjoin(StudentMLInput, Student.id == StudentMLInput.student_id)
            .where(
                and_(
                    Student.school_id == school_id,
                    Student.current_class == class_level,
                    Student.is_active == True,
                )
            )
            .order_by(Student.first_name, Student.last_name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        students = []
        for r in rows:
            # Determine gender string from enum
            gender_str = "Male"
            if r.gender:
                g = r.gender.value.upper() if hasattr(r.gender, 'value') else str(r.gender).upper()
                if g in ("FEMALE", "F"):
                    gender_str = "Female"

            # Handle NULL values from LEFT JOIN (when no ML input exists)
            # Use defaults from feature_builder
            students.append({
                "student_id": r.student_id,
                "student_name": f"{r.first_name} {r.last_name}",
                "admission_no": r.admission_no,
                "current_class": r.current_class,
                "section": r.section,
                "gender": gender_str,
                # ML input features with defaults for NULL
                "age": r.age if r.age is not None else 14,
                "attendance_pct": r.attendance_pct if r.attendance_pct is not None else 90.0,
                "avg_marks": r.avg_marks if r.avg_marks is not None else 50.0,
                "previous_failures": r.previous_failures if r.previous_failures is not None else 0,
                "family_income_monthly": r.family_income_monthly if r.family_income_monthly is not None else 12000.0,
                "distance_to_school_km": r.distance_to_school_km if r.distance_to_school_km is not None else 2.5,
                "guardian_education": r.guardian_education if r.guardian_education is not None else "Secondary",
                "single_parent": r.single_parent if r.single_parent is not None else 0,
                "sibling_dropout": r.sibling_dropout if r.sibling_dropout is not None else 0,
                "mobile_available": r.mobile_available if r.mobile_available is not None else 1,
                "internet_access": r.internet_access if r.internet_access is not None else 0,
                "scholarship": r.scholarship if r.scholarship is not None else 0,
                "midday_meal": r.midday_meal if r.midday_meal is not None else 1,
                "study_hours_per_day": r.study_hours_per_day if r.study_hours_per_day is not None else 2.0,
                "health_risk": r.health_risk if r.health_risk is not None else "Low",
                "school_engagement_score": r.school_engagement_score if r.school_engagement_score is not None else 0.5,
                "teacher_feedback_score": r.teacher_feedback_score if r.teacher_feedback_score is not None else 0.5,
                "disciplinary_incidents": r.disciplinary_incidents if r.disciplinary_incidents is not None else 0,
            })

        logger.info(
            "Fetched %d students for school=%d class=%d with ML input",
            len(students), school_id, class_level,
        )
        return students

    async def delete_old_predictions(
        self, before: datetime
    ) -> int:
        """Delete predictions older than given timestamp."""
        stmt = delete(StudentPrediction).where(
            StudentPrediction.predicted_at < before
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        logger.info("Deleted %d old prediction records", result.rowcount)
        return result.rowcount
