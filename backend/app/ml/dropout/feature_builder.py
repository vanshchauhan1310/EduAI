"""
Feature Builder — Converts database student records into model-compatible DataFrames.

Maps SQLAlchemy Student + Attendance + Assessment data to the 20-feature set
expected by the trained XGBoost pipeline:

    gender, class_level, age, attendance_pct, avg_marks,
    previous_failures, family_income_monthly, distance_to_school_km,
    guardian_education, single_parent, sibling_dropout,
    mobile_available, internet_access, scholarship, midday_meal,
    study_hours_per_day, health_risk, school_engagement_score,
    teacher_feedback_score, disciplinary_incidents
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Canonical feature order the model expects (must match model.pkl training columns)
MODEL_FEATURES: list[str] = [
    "gender",
    "class_level",
    "age",
    "attendance_pct",
    "avg_marks",
    "previous_failures",
    "family_income_monthly",
    "distance_to_school_km",
    "guardian_education",
    "single_parent",
    "sibling_dropout",
    "mobile_available",
    "internet_access",
    "scholarship",
    "midday_meal",
    "study_hours_per_day",
    "health_risk",
    "school_engagement_score",
    "teacher_feedback_score",
    "disciplinary_incidents",
]

# ─── Defaults (used when DB has no data for a field) ───────────
_DEFAULTS = {
    "family_income_monthly": 12000,       # median Indian rural household
    "distance_to_school_km": 2.5,         # average rural distance
    "guardian_education": "Secondary",
    "single_parent": 0,
    "sibling_dropout": 0,
    "mobile_available": 1,
    "study_hours_per_day": 2.0,
    "school_engagement_score": 0.5,
    "teacher_feedback_score": 0.5,
    "disciplinary_incidents": 0,
}


def _calculate_age(dob: date | None) -> int:
    """Calculate age from date of birth."""
    if dob is None:
        return 14
    ref = date.today()
    age = ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))
    return max(6, min(age, 20))


def _compute_attendance_pct(attendance_records: list[dict[str, Any]]) -> float:
    """Compute attendance percentage from attendance records."""
    if not attendance_records:
        return 90.0  # default assumption

    total = len(attendance_records)
    absent_statuses = {"ABSENT", "HALF_DAY", "LEAVE"}
    present = sum(
        1 for r in attendance_records if r.get("status") not in absent_statuses
    )
    return round((present / total) * 100, 2) if total > 0 else 90.0


def _compute_academic_stats(
    assessment_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute average marks and failure count from assessment results."""
    if not assessment_results:
        return {"avg_marks": 50.0, "previous_failures": 0}

    all_percentages: list[float] = []
    failures = 0

    for r in assessment_results:
        pct = r.get("percentage")
        if pct is not None:
            val = float(pct)
            all_percentages.append(val)
            if val < 33.0:
                failures += 1

    avg = round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 50.0

    return {
        "avg_marks": avg,
        "previous_failures": failures,
    }


def _map_health_risk(
    has_disability: bool,
    attendance_pct: float,
) -> str:
    """Map student attributes to health_risk category."""
    if has_disability:
        return "High"
    if attendance_pct < 70:
        return "High"
    if attendance_pct < 85:
        return "Medium"
    return "Low"


def _map_gender(db_gender: str | None) -> str:
    """Map DB gender enum to model expected values."""
    if db_gender is None:
        return "Male"
    g = db_gender.upper()
    if g in ("FEMALE", "F"):
        return "Female"
    return "Male"


def build_feature_row(
    student: dict[str, Any],
    attendance_records: list[dict[str, Any]] | None = None,
    assessment_results: list[dict[str, Any]] | None = None,
    school_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a single feature row from a student record and related data.

    Parameters
    ----------
    student : dict
        Flattened student record with keys matching Student model columns.
        Expected: date_of_birth, gender, current_class, has_disability,
                  receives_scholarship, receives_midday_meal
    attendance_records : list[dict], optional
        Attendance records for the student.
    assessment_results : list[dict], optional
        Assessment results for the student.
    school_info : dict, optional
        School record (used for infrastructure flags).

    Returns
    -------
    dict
        Feature dictionary matching MODEL_FEATURES.
    """
    attendance_pct = _compute_attendance_pct(attendance_records or [])
    academic_stats = _compute_academic_stats(assessment_results or [])
    age = _calculate_age(student.get("date_of_birth"))

    # Map boolean/string flags
    internet_access = 1 if (school_info or {}).get("has_computer_lab", False) else 0
    scholarship = 1 if student.get("receives_scholarship", False) else 0
    midday_meal = 1 if student.get("receives_midday_meal", True) else 0
    health_risk = _map_health_risk(
        student.get("has_disability", False),
        attendance_pct,
    )

    # Compute a simple engagement score from available data
    # Higher attendance + fewer absences = higher engagement
    school_engagement = round(min(attendance_pct / 100.0, 1.0), 4)

    # Teacher feedback placeholder (no direct DB mapping)
    teacher_feedback = 0.5

    features = {
        "gender": _map_gender(student.get("gender")),
        "class_level": student.get("current_class", 1),
        "age": age,
        "attendance_pct": attendance_pct,
        "avg_marks": academic_stats["avg_marks"],
        "previous_failures": academic_stats["previous_failures"],
        "family_income_monthly": _DEFAULTS["family_income_monthly"],
        "distance_to_school_km": _DEFAULTS["distance_to_school_km"],
        "guardian_education": _DEFAULTS["guardian_education"],
        "single_parent": _DEFAULTS["single_parent"],
        "sibling_dropout": _DEFAULTS["sibling_dropout"],
        "mobile_available": _DEFAULTS["mobile_available"],
        "internet_access": internet_access,
        "scholarship": scholarship,
        "midday_meal": midday_meal,
        "study_hours_per_day": _DEFAULTS["study_hours_per_day"],
        "health_risk": health_risk,
        "school_engagement_score": school_engagement,
        "teacher_feedback_score": teacher_feedback,
        "disciplinary_incidents": _DEFAULTS["disciplinary_incidents"],
    }

    return features


def build_features_batch(
    students_data: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Build a feature DataFrame from a batch of student records.

    Parameters
    ----------
    students_data : list[dict]
        Each dict must contain keys for student fields plus:
        - _attendance_records: list of attendance dicts
        - _assessment_results: list of assessment dicts
        - _school_info: dict of school fields

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per student, columns matching MODEL_FEATURES.
    """
    rows = []

    for record in students_data:
        attendance = record.pop("_attendance_records", [])
        assessments = record.pop("_assessment_results", [])
        school = record.pop("_school_info", None)

        feature_row = build_feature_row(
            student=record,
            attendance_records=attendance,
            assessment_results=assessments,
            school_info=school,
        )
        rows.append(feature_row)

    df = pd.DataFrame(rows, columns=MODEL_FEATURES)

    logger.info(
        "Built feature DataFrame: %d students, %d features",
        len(df),
        len(MODEL_FEATURES),
    )

    return df