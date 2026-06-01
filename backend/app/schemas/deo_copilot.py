"""
DEO Copilot Pydantic schemas for request/response validation.
"""
from typing import Any
from pydantic import BaseModel, Field


# ─── District Intelligence Brief ─────────────────────────────────

class DistrictBriefResponse(BaseModel):
    id: int | None = None
    district_id: int
    district_name: str = ""
    brief_date: str
    total_schools: int = 0
    total_students: int = 0
    total_teachers: int = 0
    active_mandals: int = 0
    avg_attendance: float = 0.0
    teacher_vacancies: int = 0
    high_risk_schools: int = 0
    dropout_risk_schools: int = 0
    content: dict = Field(default_factory=dict)
    created_at: str = ""
    model_config = {"from_attributes": True}


# ─── Risk Monitor ────────────────────────────────────────────────

class RiskAlertResponse(BaseModel):
    id: int
    risk_type: str
    severity: str
    entity_type: str | None = None
    entity_name: str | None = None
    title: str
    description: str | None = None
    risk_score: float = 0.0
    is_resolved: bool = False
    created_at: str
    model_config = {"from_attributes": True}


class RiskMonitorResponse(BaseModel):
    id: int | None = None
    district_id: int
    district_name: str
    critical_schools: int = 0
    high_risk_mandals: int = 0
    dropout_hotspots: list[str] = []
    risk_summary: dict = Field(default_factory=dict)
    alerts: list[RiskAlertResponse] = []
    ai_analysis: str = ""
    created_at: str = ""


# ─── Teacher Rationalization ────────────────────────────────────

class RationalizationSchoolResult(BaseModel):
    school_id: int
    school_name: str
    dise_code: str = ""
    enrollment: int = 0
    current_teachers: int = 0
    required_teachers: int = 0
    shortage: int = 0
    surplus: int = 0
    subject_gaps: list[str] = []
    priority: str = "LOW"


class TeacherRationalizationResponse(BaseModel):
    id: int | None = None
    district_id: int
    district_name: str
    total_surplus: int = 0
    total_deficit: int = 0
    schools_analyzed: int = 0
    schools: list[RationalizationSchoolResult] = []
    ai_recommendations: str = ""
    created_at: str = ""


class RationalizationPlanRequest(BaseModel):
    district_id: int | None = None
    context: str | None = None


# ─── Governance Communication ────────────────────────────────────

class CommunicationTemplateInfo(BaseModel):
    key: str
    name: str
    description: str
    fields: list[dict[str, Any]]


class CommunicationGenerateRequest(BaseModel):
    communication_type: str = Field(..., description="Template key")
    template_fields: dict[str, Any] = Field(..., description="Form field values")
    language: str = Field(default="English")


class CommunicationGenerateResponse(BaseModel):
    id: int
    communication_type: str
    subject: str
    priority: str
    target_audience: str
    content: str
    reference_number: str | None = None
    created_at: str
    model_config = {"from_attributes": True}


class CommunicationHistoryItem(BaseModel):
    id: int
    communication_type: str
    subject: str
    priority: str
    created_at: str