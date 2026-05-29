from datetime import date
from pydantic import BaseModel, Field
from app.models.attendance import AttendanceStatus, AttendanceReferenceType


class AttendanceMarkRequest(BaseModel):
    reference_type: AttendanceReferenceType
    reference_id: int
    school_id: int
    date: date
    status: AttendanceStatus
    session: str = "FULL"
    class_id: int | None = None
    section: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    remarks: str | None = None


class BulkAttendanceItem(BaseModel):
    reference_id: int
    status: AttendanceStatus
    remarks: str | None = None


class BulkAttendanceRequest(BaseModel):
    reference_type: AttendanceReferenceType
    school_id: int
    class_id: int | None = None
    section: str | None = None
    date: date
    session: str = "FULL"
    records: list[BulkAttendanceItem] = Field(..., min_length=1)
    latitude: float | None = None
    longitude: float | None = None


class AttendanceResponse(BaseModel):
    id: int
    reference_type: str
    reference_id: int
    school_id: int
    date: date
    status: str
    session: str
    latitude: float | None
    longitude: float | None
    is_geo_verified: bool
    remarks: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    half_days: int
    attendance_percentage: float
    consecutive_absences: int
    last_absent_date: date | None


class ClassAttendanceSummary(BaseModel):
    school_id: int
    class_id: int
    section: str | None
    date: date
    total_students: int
    present: int
    absent: int
    late: int
    attendance_rate: float


class AttendanceAnalyticsRequest(BaseModel):
    school_id: int | None = None
    mandal_id: int | None = None
    district_id: int | None = None
    from_date: date
    to_date: date
    reference_type: AttendanceReferenceType = AttendanceReferenceType.STUDENT
