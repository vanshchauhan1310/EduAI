"""
DropoutPredictionService — Orchestrates the full ML prediction pipeline.

Pipeline:
  Supabase (students + attendance + assessments)
      → Feature Builder
      → student_ml_input table (persist features)  ← NEW
      → ML Predictor (reads from student_ml_input)
      → student_predictions table (save output)    ← NEW
      → Dashboard APIs (JOIN with students for names)

All dashboard queries JOIN student_predictions with students table
to include student_name, admission_no in responses.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.school import School
from app.models.attendance import Attendance, AttendanceReferenceType, AttendanceStatus
from app.models.assessment import AssessmentResult, Assessment, AssessmentType
from app.models.student_ml_input import StudentMLInput
from app.models.student_prediction import StudentPrediction
from app.repositories.dropout_prediction_repository import (
    DropoutPredictionRepository,
)
from app.ai.dropout.recommendation_engine import get_recommendation as get_deep_recommendations
from app.ml.dropout.feature_builder import build_feature_row, build_features_batch
from app.ml.dropout.predictor import (
    predict_single,
    predict_batch,
    reload_model,
)

logger = logging.getLogger(__name__)


class DropoutPredictionService:
    """Business logic layer for dropout predictions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DropoutPredictionRepository(db)

    # ═════════════════════════════════════════════════════════════
    # Pipeline: Run Predictions (2-step: save input features → predict)
    # ═════════════════════════════════════════════════════════════

    async def run_predictions(
        self,
        school_id: int | None = None,
        academic_year: str | None = None,
        batch_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full prediction pipeline for active students.

        Step 1: Build features from DB → save to student_ml_input table
        Step 2: Read features from student_ml_input → ML predict
        Step 3: Save predictions to student_predictions table

        Returns summary stats (no student names — that's a JOIN concern for APIs).
        """
        batch_id = batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(
            "Starting prediction pipeline — batch=%s school=%s year=%s",
            batch_id,
            school_id,
            academic_year,
        )

        # 1. Fetch active students
        students = await self._fetch_students(school_id, academic_year)
        if not students:
            logger.warning("No active students found for prediction.")
            return {
                "batch_id": batch_id,
                "total_students": 0,
                "high_risk_count": 0,
                "critical_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
            }

        # 2. Build features for each student
        enriched_records: list[dict[str, Any]] = []
        student_ids: list[int] = []

        for student in students:
            attendance_records = await self._fetch_attendance(student.id)
            assessment_results = await self._fetch_assessments(student.id)
            school_info = await self._fetch_school_info(student.school_id)

            record = {
                "date_of_birth": student.date_of_birth,
                "gender": student.gender,
                "current_class": student.current_class,
                "has_disability": student.has_disability or False,
                "receives_scholarship": student.receives_scholarship or False,
                "receives_midday_meal": student.receives_midday_meal or True,
                "_attendance_records": attendance_records,
                "_assessment_results": assessment_results,
                "_school_info": school_info,
            }
            enriched_records.append(record)
            student_ids.append(student.id)

        # 3. Build feature DataFrame
        features_df = build_features_batch(enriched_records)

        # 4. Persist features to student_ml_input table (Step 1)
        ml_inputs: list[dict[str, Any]] = []
        for i, (_, row) in enumerate(features_df.iterrows()):
            ml_input = {
                "student_id": student_ids[i],
                "gender": str(row.get("gender", "Male")),
                "class_level": int(row.get("class_level", 1)),
                "age": int(row.get("age", 14)),
                "attendance_pct": float(row.get("attendance_pct", 90.0)),
                "avg_marks": float(row.get("avg_marks", 50.0)),
                "previous_failures": int(row.get("previous_failures", 0)),
                "family_income_monthly": float(row.get("family_income_monthly", 12000.0)),
                "distance_to_school_km": float(row.get("distance_to_school_km", 2.5)),
                "guardian_education": str(row.get("guardian_education", "Secondary")),
                "single_parent": int(row.get("single_parent", 0)),
                "sibling_dropout": int(row.get("sibling_dropout", 0)),
                "mobile_available": int(row.get("mobile_available", 1)),
                "internet_access": int(row.get("internet_access", 0)),
                "scholarship": int(row.get("scholarship", 0)),
                "midday_meal": int(row.get("midday_meal", 1)),
                "study_hours_per_day": float(row.get("study_hours_per_day", 2.0)),
                "health_risk": str(row.get("health_risk", "Low")),
                "school_engagement_score": float(row.get("school_engagement_score", 0.5)),
                "teacher_feedback_score": float(row.get("teacher_feedback_score", 0.5)),
                "disciplinary_incidents": int(row.get("disciplinary_incidents", 0)),
            }
            ml_inputs.append(ml_input)

        await self.repo.bulk_upsert_ml_input(ml_inputs)
        logger.info("Persisted %d feature records to student_ml_input", len(ml_inputs))

        # 5. Run batch ML prediction (Step 2)
        predictions_df = predict_batch(features_df)

        # 6. Save results to student_predictions table (Step 3)
        now = datetime.utcnow()
        prediction_records: list[StudentPrediction] = []

        for i, (_, row) in enumerate(predictions_df.iterrows()):
            pred = StudentPrediction(
                student_id=student_ids[i],
                dropout_probability=float(row["dropout_probability"]),
                risk_level=str(row["risk_level"]),
                recommendation=str(row["recommendation"]),
                model_version="xgboost_v1.0",
                predicted_at=now,
                batch_id=batch_id,
            )
            prediction_records.append(pred)

        await self.repo.bulk_create_predictions(prediction_records)

        # Compute summary
        risk_counts = predictions_df["risk_level"].value_counts()

        summary = {
            "batch_id": batch_id,
            "total_students": len(students),
            "high_risk_count": int(risk_counts.get("High", 0)),
            "critical_risk_count": int(risk_counts.get("Critical", 0)),
            "medium_risk_count": int(risk_counts.get("Medium", 0)),
            "low_risk_count": int(risk_counts.get("Low", 0)),
        }

        logger.info("Prediction pipeline complete — %s", summary)
        return summary

    # ═════════════════════════════════════════════════════════════
    # Dashboard Queries (All JOIN with students for names)
    # ═════════════════════════════════════════════════════════════

    async def get_high_risk_students(
        self,
        school_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return high-risk / critical-risk students (HM dashboard)."""
        items, total = await self.repo.get_high_risk_students(
            school_id=school_id, limit=limit, offset=offset
        )
        return {"total": total, "students": items}

    async def get_student_prediction(
        self, student_id: int
    ) -> dict[str, Any] | None:
        """
        Return latest prediction for a student, enriched with name/school.
        JOINs: student_predictions → students → schools
        """
        return await self.repo.get_latest_prediction_by_student(student_id)

    async def get_school_analysis(self, school_id: int) -> dict[str, Any] | None:
        """School-level analysis (MEO dashboard)."""
        summary = await self.repo.get_school_summary(school_id)
        if summary is None:
            return None

        students = await self.repo.get_school_students(school_id)

        return {
            "summary": summary,
            "students": students,
        }

    async def get_mandal_analysis(self, mandal_id: int) -> dict[str, Any] | None:
        """Mandal-level analysis (MEO/DEO dashboard)."""
        return await self.repo.get_mandal_summary(mandal_id)

    async def get_district_analysis(self, district_id: int) -> dict[str, Any] | None:
        """District-level analysis (DEO dashboard)."""
        return await self.repo.get_district_summary(district_id)

    # ═════════════════════════════════════════════════════════════
    # Class-Wise Prediction (HM Dashboard — NEW)
    # ═════════════════════════════════════════════════════════════

    async def predict_by_class(
        self,
        school_id: int,
        class_level: int,
    ) -> dict[str, Any]:
        """
        Run dropout predictions for all students in a given school+class.

        Instead of building features from scratch (attendance, assessments),
        this method reads the already-computed features from the
        student_ml_input table — which is auto-populated via event listeners
        when students are created/updated.

        Pipeline:
          1. Fetch all active students in school+class JOINed with their ML input
          2. Build feature DataFrame from stored ML input
          3. Run ML predictions
          4. Save predictions to student_predictions table
          5. Return enriched results with student names

        This is the HM-friendly flow: pick a class → get predictions instantly.
        """
        batch_id = f"class_{school_id}_{class_level}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(
            "Starting class-wise prediction — school=%d class=%d batch=%s",
            school_id, class_level, batch_id,
        )

        # 1. Fetch students with ML input data
        students_with_features = await self.repo.get_students_by_class_with_ml_input(
            school_id=school_id,
            class_level=class_level,
        )

        if not students_with_features:
            logger.warning(
                "No students found with ML input for school=%d class=%d",
                school_id, class_level,
            )
            return {
                "batch_id": batch_id,
                "school_id": school_id,
                "class_level": class_level,
                "total_students": 0,
                "high_risk_count": 0,
                "critical_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "students": [],
                "message": f"No students found in Class {class_level} with ML features available.",
            }

        # 2. Build feature DataFrame from stored ML input
        import pandas as pd
        from app.ml.dropout.feature_builder import MODEL_FEATURES

        feature_rows = []
        for s in students_with_features:
            row = {
                "gender": s["gender"],
                "class_level": s["current_class"],
                "age": s["age"],
                "attendance_pct": s["attendance_pct"],
                "avg_marks": s["avg_marks"],
                "previous_failures": s["previous_failures"],
                "family_income_monthly": s["family_income_monthly"],
                "distance_to_school_km": s["distance_to_school_km"],
                "guardian_education": s["guardian_education"],
                "single_parent": s["single_parent"],
                "sibling_dropout": s["sibling_dropout"],
                "mobile_available": s["mobile_available"],
                "internet_access": s["internet_access"],
                "scholarship": s["scholarship"],
                "midday_meal": s["midday_meal"],
                "study_hours_per_day": s["study_hours_per_day"],
                "health_risk": s["health_risk"],
                "school_engagement_score": s["school_engagement_score"],
                "teacher_feedback_score": s["teacher_feedback_score"],
                "disciplinary_incidents": s["disciplinary_incidents"],
            }
            feature_rows.append(row)

        features_df = pd.DataFrame(feature_rows, columns=MODEL_FEATURES)

        # 3. Run ML predictions
        from app.ml.dropout.predictor import predict_batch
        predictions_df = predict_batch(features_df)

        # 4. Save predictions to student_predictions table
        now = datetime.utcnow()
        prediction_records: list[StudentPrediction] = []
        saved_recommendations: list[tuple[str, list[str]]] = []

        for i, (_, row) in enumerate(predictions_df.iterrows()):
            student_id = students_with_features[i]["student_id"]
            student_features = students_with_features[i]
            recommendations = get_deep_recommendations(student_features, str(row["risk_level"]))
            recommendation_text = " | ".join(recommendations) if recommendations else str(row["recommendation"])

            pred = StudentPrediction(
                student_id=student_id,
                dropout_probability=float(row["dropout_probability"]),
                risk_level=str(row["risk_level"]),
                recommendation=recommendation_text,
                model_version="xgboost_v1.0",
                predicted_at=now,
                batch_id=batch_id,
            )
            prediction_records.append(pred)
            saved_recommendations.append((recommendation_text, recommendations))

        await self.repo.bulk_create_predictions(prediction_records)

        # 5. Build enriched response
        student_results = []
        for i, s in enumerate(students_with_features):
            pred_row = predictions_df.iloc[i]
            recommendation_text, recommendations = saved_recommendations[i]

            student_results.append({
                "student_id": s["student_id"],
                "student_name": s["student_name"],
                "admission_no": s["admission_no"],
                "current_class": s["current_class"],
                "section": s.get("section"),
                "gender": s["gender"],
                "age": s["age"],
                "attendance_pct": s["attendance_pct"],
                "avg_marks": s["avg_marks"],
                "dropout_probability": float(pred_row["dropout_probability"]),
                "risk_level": str(pred_row["risk_level"]),
                "recommendation": recommendation_text,
                "recommendations": recommendations,
            })

        # Risk counts
        risk_levels = [r["risk_level"] for r in student_results]
        high_count = sum(1 for lv in risk_levels if lv == "High")
        critical_count = sum(1 for lv in risk_levels if lv == "Critical")
        medium_count = sum(1 for lv in risk_levels if lv == "Medium")
        low_count = sum(1 for lv in risk_levels if lv == "Low")

        result = {
            "batch_id": batch_id,
            "school_id": school_id,
            "class_level": class_level,
            "total_students": len(student_results),
            "high_risk_count": high_count,
            "critical_risk_count": critical_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "students": student_results,
            "message": f"Predictions completed for {len(student_results)} students in Class {class_level}.",
        }

        logger.info(
            "Class-wise prediction complete — school=%d class=%d students=%d high=%d critical=%d",
            school_id, class_level, result["total_students"],
            result["high_risk_count"], result["critical_risk_count"],
        )
        return result

    # ═════════════════════════════════════════════════════════════
    # ML Input Feature Queries
    # ═════════════════════════════════════════════════════════════

    async def get_student_ml_input(
        self, student_id: int
    ) -> dict[str, Any] | None:
        """Get the stored ML input features for a student."""
        return await self.repo.get_ml_input(student_id)

    # ═════════════════════════════════════════════════════════════
    # Cron Entry Point
    # ═════════════════════════════════════════════════════════════

    async def run_daily_predictions(self) -> dict[str, Any]:
        """
        Cron-ready function for scheduled daily predictions.
        Runs predictions for all active students across all schools.
        """
        logger.info("=== Daily Dropout Prediction Cron Started ===")

        try:
            result = await self.run_predictions(
                school_id=None,
                academic_year=None,
                batch_id=f"daily_{datetime.utcnow().strftime('%Y%m%d')}",
            )

            logger.info(
                "=== Daily Dropout Prediction Cron Complete: %d students, "
                "%d high-risk, %d critical ===",
                result["total_students"],
                result["high_risk_count"],
                result["critical_risk_count"],
            )
            return result

        except Exception as e:
            logger.error("Daily prediction cron failed: %s", str(e), exc_info=True)
            raise

    # ═════════════════════════════════════════════════════════════
    # Private Helpers
    # ═════════════════════════════════════════════════════════════

    async def _fetch_students(
        self,
        school_id: int | None = None,
        academic_year: str | None = None,
    ) -> list[Student]:
        """Fetch all active students, optionally filtered."""
        conditions = [Student.is_active == True]

        if school_id:
            conditions.append(Student.school_id == school_id)
        if academic_year:
            conditions.append(Student.academic_year == academic_year)

        result = await self.db.execute(
            select(Student).where(and_(*conditions)).order_by(Student.id)
        )
        students = list(result.scalars().all())

        logger.info("Fetched %d active students", len(students))
        return students

    async def _fetch_attendance(self, student_id: int) -> list[dict[str, Any]]:
        """Fetch attendance records for a student."""
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.reference_type == AttendanceReferenceType.STUDENT,
                    Attendance.reference_id == student_id,
                )
            ).order_by(Attendance.date)
        )
        records = result.scalars().all()

        return [
            {
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "date": r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date),
            }
            for r in records
        ]

    async def _fetch_assessments(self, student_id: int) -> list[dict[str, Any]]:
        """Fetch assessment results for a student."""
        result = await self.db.execute(
            select(AssessmentResult, Assessment)
            .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
            .where(AssessmentResult.student_id == student_id)
            .order_by(Assessment.conducted_date)
        )
        rows = result.all()

        return [
            {
                "marks_obtained": ar.marks_obtained,
                "percentage": ar.percentage,
                "assessment_type": a.assessment_type.value if hasattr(a.assessment_type, "value") else str(a.assessment_type),
                "max_marks": a.max_marks,
            }
            for ar, a in rows
        ]

    async def _fetch_school_info(self, school_id: int) -> dict[str, Any] | None:
        """Fetch school infrastructure info."""
        result = await self.db.execute(
            select(School).where(School.id == school_id)
        )
        school = result.scalar_one_or_none()
        if school is None:
            return None

        return {
            "has_computer_lab": school.has_computer_lab,
            "has_electricity": school.has_electricity,
            "has_library": school.has_library,
            "has_playground": school.has_playground,
        }