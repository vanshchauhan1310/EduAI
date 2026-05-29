from datetime import date
from pydantic import BaseModel


class DistrictAnalyticsResponse(BaseModel):
    district_id: int
    district_name: str
    total_schools: int
    total_students: int
    total_teachers: int
    overall_attendance_rate: float
    dropout_rate: float
    avg_school_health_score: float
    high_risk_students: int
    schools_below_threshold: int
    monthly_trends: list[dict]


class SchoolHealthSummary(BaseModel):
    school_id: int
    school_name: str
    dise_code: str
    health_score: float
    attendance_rate: float
    dropout_risk_count: int
    total_students: int
    total_teachers: int
    teacher_student_ratio: float
    infrastructure_score: float
    mandal_name: str


class ClusterAnalyticsResponse(BaseModel):
    mandal_id: int
    mandal_name: str
    total_schools: int
    total_students: int
    avg_attendance_rate: float
    schools_health: list[SchoolHealthSummary]
    top_performers: list[dict]
    bottom_performers: list[dict]


class AttendanceTrendPoint(BaseModel):
    date: date
    attendance_rate: float
    present_count: int
    absent_count: int


class PerformanceTrendPoint(BaseModel):
    assessment_type: str
    subject: str
    avg_percentage: float
    pass_rate: float
    date: date


class GovernanceReportResponse(BaseModel):
    report_date: date
    district_id: int
    period: str  # "2024-25 Q2"
    summary: dict
    school_rankings: list[dict]
    intervention_required: list[dict]
    achievements: list[dict]
    ai_recommendations: list[str]
