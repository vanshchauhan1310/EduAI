"""
Pydantic v2 schemas for the governance layer (auth, users, schools, attendance).
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from core.roles import Role


# ── Auth ──────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: Role
    school_id: Optional[int] = None
    student_id: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: int
    school_id: Optional[int] = None
    student_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Schools ───────────────────────────────────────────────────────────────────
class SchoolCreate(BaseModel):
    name: str
    udise_code: Optional[str] = None
    district: Optional[str] = None
    mandal: Optional[str] = None
    address: Optional[str] = None


class SchoolOut(BaseModel):
    id: int
    name: str
    udise_code: Optional[str] = None
    district: Optional[str] = None
    mandal: Optional[str] = None
    health_score: float
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Attendance ────────────────────────────────────────────────────────────────
class AttendanceMark(BaseModel):
    student_id: int
    school_id: int
    date: str = Field(description="YYYY-MM-DD")
    status: str = Field(default="present", description="present | absent | late")


class AttendanceBulkMark(BaseModel):
    school_id: int
    date: str
    records: List["AttendanceStudentStatus"]


class AttendanceStudentStatus(BaseModel):
    student_id: int
    status: str = "present"


class AttendanceOut(BaseModel):
    id: int
    student_id: int
    school_id: int
    date: str
    status: str
    marked_by: Optional[int] = None

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    student_id: int
    total_days: int
    present: int
    absent: int
    late: int
    attendance_percentage: float


AttendanceBulkMark.model_rebuild()
