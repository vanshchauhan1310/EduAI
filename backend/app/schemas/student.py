from datetime import date
from pydantic import BaseModel, Field
from app.models.student import Gender, RiskLevel


class StudentCreateRequest(BaseModel):
    admission_no: str = Field(..., min_length=3)
    aadhaar_no: str | None = Field(None, pattern=r"^\d{12}$")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date | None = None
    gender: Gender
    category: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    parent_email: str | None = None
    current_class: int = Field(..., ge=1, le=12)
    section: str | None = None
    academic_year: str
    school_id: int
    enrollment_date: date | None = None
    receives_midday_meal: bool = True
    receives_scholarship: bool = False
    has_disability: bool = False


class StudentUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    parent_email: str | None = None
    current_class: int | None = Field(None, ge=1, le=12)
    section: str | None = None
    category: str | None = None
    receives_midday_meal: bool | None = None
    receives_scholarship: bool | None = None
    has_disability: bool | None = None


class StudentResponse(BaseModel):
    id: int
    admission_no: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date | None
    gender: str
    category: str | None
    parent_name: str | None
    parent_phone: str | None
    current_class: int
    section: str | None
    academic_year: str
    school_id: int
    dropout_risk_score: float | None
    risk_level: str
    is_active: bool
    enrollment_date: date | None
    created_at: str

    model_config = {"from_attributes": True}


class StudentPerformanceSummary(BaseModel):
    student_id: int
    full_name: str
    attendance_percentage: float
    average_marks: float | None
    rank_in_class: int | None
    risk_level: str
    consecutive_absences: int
    assessments_taken: int


class StudentFilterRequest(BaseModel):
    school_id: int | None = None
    class_grade: int | None = None
    section: str | None = None
    risk_level: RiskLevel | None = None
    gender: Gender | None = None
    academic_year: str | None = None
    is_active: bool = True
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
