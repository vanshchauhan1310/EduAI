"""
SQLAlchemy event listeners for automatic ML feature computation.

When a new Student is inserted:
  1. Computes 20 model features from student + attendance + assessments + school
  2. Saves features to student_ml_input table

This ensures student_ml_input is always in sync with the students table.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session as SyncSession

from app.models.student import Student
from app.models.school import School
from app.models.attendance import Attendance, AttendanceReferenceType
from app.models.assessment import AssessmentResult, Assessment
from app.models.student_ml_input import StudentMLInput
from app.database.session import Base

logger = logging.getLogger(__name__)

# ─── Defaults for features not directly in DB ────────────────
_DEFAULTS = {
    "family_income_monthly": 12000.0,
    "distance_to_school_km": 2.5,
    "guardian_education": "Secondary",
    "single_parent": 0,
    "sibling_dropout": 0,
    "mobile_available": 1,
    "study_hours_per_day": 2.0,
    "school_engagement_score": 0.5,
    "teacher_feedback_score": 0.5,
    "disciplinary_incidents": 0,
}


def _compute_features(student: Student) -> dict[str, Any]:
    """
    Compute the 20 ML features from a Student object and its relationships.
    Runs synchronously inside the same transaction that inserted the student.
    """
    from datetime import date

    # 1. Age from DOB
    age = 14
    if student.date_of_birth:
        ref = date.today()
        age = ref.year - student.date_of_birth.year - (
            (ref.month, ref.day) < (student.date_of_birth.month, student.date_of_birth.day)
        )
        age = max(6, min(age, 20))

    # 2. Attendance percentage
    attendance_pct = 90.0
    if student.id:
        from sqlalchemy.orm import Session as SyncSession
        session = SyncSession.object_session(student)
        if session:
            att_records = session.query(Attendance).filter(
                Attendance.reference_type == AttendanceReferenceType.STUDENT,
                Attendance.reference_id == student.id,
            ).all()
            if att_records:
                absent_statuses = {"ABSENT", "HALF_DAY", "LEAVE"}
                total = len(att_records)
                present = sum(
                    1 for r in att_records
                    if (r.status.value if hasattr(r.status, 'value') else str(r.status)) not in absent_statuses
                )
                attendance_pct = round((present / total) * 100, 2) if total > 0 else 90.0

    # 3. Academic stats
    avg_marks = 50.0
    previous_failures = 0
    if student.id:
        session = SyncSession.object_session(student)
        if session:
            results = session.query(AssessmentResult).filter(
                AssessmentResult.student_id == student.id
            ).all()
            if results:
                percentages = [float(r.percentage) for r in results if r.percentage is not None]
                if percentages:
                    avg_marks = round(sum(percentages) / len(percentages), 2)
                    previous_failures = sum(1 for p in percentages if p < 33.0)

    # 4. School info
    internet_access = 0
    if student.school:
        internet_access = 1 if student.school.has_computer_lab else 0
    elif student.school_id:
        session = SyncSession.object_session(student)
        if session:
            school = session.query(School).filter(School.id == student.school_id).first()
            if school:
                internet_access = 1 if school.has_computer_lab else 0

    # 5. Health risk
    health_risk = "Low"
    if student.has_disability:
        health_risk = "High"
    elif attendance_pct < 70:
        health_risk = "High"
    elif attendance_pct < 85:
        health_risk = "Medium"

    # 6. School engagement
    school_engagement = round(min(attendance_pct / 100.0, 1.0), 4)

    # 7. Gender mapping
    gender = "Male"
    if student.gender:
        g = student.gender.value.upper() if hasattr(student.gender, 'value') else str(student.gender).upper()
        if g in ("FEMALE", "F"):
            gender = "Female"

    return {
        "student_id": student.id,
        "gender": gender,
        "class_level": student.current_class or 1,
        "age": age,
        "attendance_pct": attendance_pct,
        "avg_marks": avg_marks,
        "previous_failures": previous_failures,
        "family_income_monthly": _DEFAULTS["family_income_monthly"],
        "distance_to_school_km": _DEFAULTS["distance_to_school_km"],
        "guardian_education": _DEFAULTS["guardian_education"],
        "single_parent": _DEFAULTS["single_parent"],
        "sibling_dropout": _DEFAULTS["sibling_dropout"],
        "mobile_available": _DEFAULTS["mobile_available"],
        "internet_access": internet_access,
        "scholarship": 1 if student.receives_scholarship else 0,
        "midday_meal": 1 if student.receives_midday_meal else 0,
        "study_hours_per_day": _DEFAULTS["study_hours_per_day"],
        "health_risk": health_risk,
        "school_engagement_score": school_engagement,
        "teacher_feedback_score": _DEFAULTS["teacher_feedback_score"],
        "disciplinary_incidents": _DEFAULTS["disciplinary_incidents"],
    }


# ─── Event Listener ───────────────────────────────────────────

@event.listens_for(Student, "after_insert")
def auto_populate_ml_input(mapper, connection, target: Student):
    """
    After a new Student is inserted into the database,
    automatically compute ML features and insert into student_ml_input.
    """
    try:
        features = _compute_features(target)
        logger.info(
            "Auto-populating ML features for student %s %s (id=%d)",
            target.first_name,
            target.last_name,
            target.id,
        )

        # Insert directly via connection (not session) to avoid transaction conflicts
        from sqlalchemy import insert
        stmt = insert(StudentMLInput).values(**features)
        connection.execute(stmt)

        logger.debug(
            "ML features saved for student_id=%d: attendance=%s, marks=%s",
            target.id,
            features.get("attendance_pct"),
            features.get("avg_marks"),
        )

    except Exception as e:
        # Log but don't block student creation
        logger.error(
            "Failed to auto-populate ML features for student %d: %s",
            target.id,
            str(e),
            exc_info=True,
        )


@event.listens_for(Student, "after_update")
def auto_update_ml_input(mapper, connection, target: Student):
    """
    When a Student record is updated, also update the ML features.
    """
    try:
        features = _compute_features(target)
        logger.info(
            "Auto-updating ML features for student_id=%d",
            target.id,
        )

        from sqlalchemy import update
        stmt = (
            update(StudentMLInput)
            .where(StudentMLInput.student_id == target.id)
            .values(**features)
        )
        result = connection.execute(stmt)
        if result.rowcount == 0:
            # No existing row — insert instead
            from sqlalchemy import insert
            stmt = insert(StudentMLInput).values(**features)
            connection.execute(stmt)

        logger.debug(
            "ML features updated for student_id=%d",
            target.id,
        )

    except Exception as e:
        logger.error(
            "Failed to auto-update ML features for student %d: %s",
            target.id,
            str(e),
            exc_info=True,
        )