from datetime import date, datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    HOLIDAY = "HOLIDAY"
    LEAVE = "LEAVE"


class AttendanceReferenceType(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference_type: Mapped[AttendanceReferenceType] = mapped_column(SAEnum(AttendanceReferenceType), nullable=False)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # student_id or teacher_id
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"), nullable=False)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(SAEnum(AttendanceStatus), nullable=False)
    session: Mapped[str] = mapped_column(String(10), default="FULL")  # FULL | MORNING | AFTERNOON

    # For student attendance
    class_id: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(5))

    # Geo-verification
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_geo_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit
    marked_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    remarks: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Polymorphic reference_id has no direct FK — query attendance in service layer directly.
