"""
Pydantic schemas for Dropout Prediction APIs.

Covers:
- StudentMLInput (model input features storage)
- StudentPrediction (model output)
- All API response schemas for HM / MEO / DEO dashboards

Student name/admission_no is fetched by JOINing with students table
at the API layer — schemas below include those enriched fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── StudentMLInput Schemas ─────────────────────────────────────

class StudentMLInputBase(BaseModel):
    """The 20 features the ML model expects."""
    student_id: int
    gender: str = "Male"
    class_level: int = 1
    age: int = 14
    attendance_pct: float = 90.0
    avg_marks: float = 50.0
    previous_failures: int = 0
    family_income_monthly: float = 12000.0
    distance_to_school_km: float = 2.5
    guardian_education: str = "Secondary"
    single_parent: int = 0
    sibling_dropout: int = 0
    mobile_available: int = 1
    internet_access: int = 0
    scholarship: int = 0
    midday_meal: int = 1
    study_hours_per_day: float = 2.0
    health_risk: str = "Low"
    school_engagement_score: float = 0.5
    teacher_feedback_score: float = 0.5
    disciplinary_incidents: int = 0


class StudentMLInputResponse(StudentMLInputBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── StudentPrediction Schemas ──────────────────────────────────

class StudentPredictionBase(BaseModel):
    student_id: int
    dropout_probability: float = Field(..., description="Probability score 0-100")
    risk_level: str = Field(..., description="Low / Medium / High / Critical")
    recommendation: str


class StudentPredictionResponse(StudentPredictionBase):
    id: int
    model_version: str | None = None
    predicted_at: datetime
    batch_id: str | None = None

    model_config = {"from_attributes": True}


class StudentPredictionDetail(StudentPredictionBase):
    """Detailed prediction response including student info from JOIN."""
    prediction_id: int
    student_name: str
    admission_no: str
    school_id: int
    school_name: str
    current_class: int
    section: str | None = None
    academic_year: str
    predicted_at: datetime


# ─── Run Predictions ───────────────────────────────────────────

class RunPredictionsRequest(BaseModel):
    school_id: int | None = Field(
        None,
        description="If provided, run predictions only for this school. Otherwise, all active students.",
    )
    academic_year: str | None = Field(
        None,
        description="Filter by academic year. Defaults to current year.",
    )


class RunPredictionsResponse(BaseModel):
    message: str
    batch_id: str
    total_students: int
    high_risk_count: int
    critical_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    started_at: datetime


class PredictionStatusResponse(BaseModel):
    batch_id: str
    status: str  # "running" | "completed" | "failed"
    total_students: int | None = None
    processed: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


# ─── Class-Wise Prediction (NEW) ────────────────────────────────

class PredictByClassRequest(BaseModel):
    school_id: int | None = Field(
        None,
        description="School ID to predict for. If not provided, uses the authenticated user's school.",
    )
    class_level: int = Field(..., ge=1, le=12, description="Class level (1-12)")


class ClassPredictionStudentItem(BaseModel):
    """Single student prediction result for class-wise prediction."""
    student_id: int
    student_name: str
    admission_no: str
    current_class: int
    section: str | None = None
    gender: str
    age: int
    attendance_pct: float
    avg_marks: float
    dropout_probability: float
    risk_level: str
    recommendation: str


class PredictByClassResponse(BaseModel):
    batch_id: str
    school_id: int
    class_level: int
    total_students: int
    high_risk_count: int
    critical_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    students: list[ClassPredictionStudentItem]
    message: str


# ─── High Risk Listing ────────────────────────────────────────

class HighRiskStudentItem(BaseModel):
    prediction_id: int
    student_id: int
    student_name: str
    admission_no: str
    school_id: int
    school_name: str
    current_class: int
    dropout_probability: float
    risk_level: str
    recommendation: str
    predicted_at: datetime


class HighRiskListResponse(BaseModel):
    total: int
    students: list[HighRiskStudentItem]


# ─── School-Level Analysis (MEO Dashboard) ────────────────────

class SchoolDropoutSummary(BaseModel):
    school_id: int
    school_name: str
    total_students: int
    total_predictions: int
    high_risk_count: int
    critical_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
    top_risk_factors: list[str]
    last_prediction_at: datetime | None = None


class SchoolDropoutStudentItem(BaseModel):
    student_id: int
    student_name: str
    admission_no: str
    current_class: int
    dropout_probability: float
    risk_level: str
    recommendation: str


class SchoolDropoutDetailResponse(BaseModel):
    summary: SchoolDropoutSummary
    students: list[SchoolDropoutStudentItem]


# ─── Mandal-Level Analysis ────────────────────────────────────

class MandalSchoolItem(BaseModel):
    school_id: int
    school_name: str
    total_students: int
    high_risk_count: int
    critical_risk_count: int
    average_risk_score: float


class MandalDropoutSummary(BaseModel):
    mandal_id: int
    mandal_name: str
    district_name: str
    total_schools: int
    total_students: int
    total_high_risk: int
    total_critical_risk: int
    overall_average_risk: float
    schools: list[MandalSchoolItem]
    last_prediction_at: datetime | None = None


# ─── District-Level Analysis (DEO Dashboard) ──────────────────

class DistrictMandalItem(BaseModel):
    mandal_id: int
    mandal_name: str
    total_schools: int
    total_students: int
    high_risk_count: int
    critical_risk_count: int
    average_risk_score: float


class DistrictDropoutSummary(BaseModel):
    district_id: int
    district_name: str
    total_mandals: int
    total_schools: int
    total_students: int
    total_high_risk: int
    total_critical_risk: int
    overall_average_risk: float
    mandals: list[DistrictMandalItem]
    last_prediction_at: datetime | None = None


# ─── Generic API Response ─────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: str | None = None