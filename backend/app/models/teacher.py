from datetime import date, datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class TeacherType(str, Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    GUEST = "GUEST"
    DEPUTATION = "DEPUTATION"


class SubjectArea(str, Enum):
    MATHEMATICS = "MATHEMATICS"
    SCIENCE = "SCIENCE"
    SOCIAL = "SOCIAL"
    ENGLISH = "ENGLISH"
    TELUGU = "TELUGU"
    HINDI = "HINDI"
    PHYSICAL_EDUCATION = "PHYSICAL_EDUCATION"
    ART = "ART"
    COMPUTER_SCIENCE = "COMPUTER_SCIENCE"
    GENERAL = "GENERAL"


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"), nullable=False)

    designation: Mapped[str | None] = mapped_column(String(100))
    teacher_type: Mapped[TeacherType] = mapped_column(SAEnum(TeacherType), default=TeacherType.PERMANENT)
    subject_area: Mapped[SubjectArea] = mapped_column(SAEnum(SubjectArea), default=SubjectArea.GENERAL)
    classes_assigned: Mapped[str | None] = mapped_column(String(100))  # JSON: ["6A","7B"]

    # Professional details
    qualification: Mapped[str | None] = mapped_column(String(255))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    date_of_joining: Mapped[date | None] = mapped_column(Date)
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    # Performance
    average_attendance_pct: Mapped[float | None] = mapped_column(Float)
    performance_score: Mapped[float | None] = mapped_column(Float)  # 0–100
    last_performance_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")
    school: Mapped["School"] = relationship("School", back_populates="teachers")
    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        primaryjoin="and_(Attendance.reference_id == Teacher.id, Attendance.reference_type == 'TEACHER')",
        foreign_keys="[Attendance.reference_id]",
        uselist=True,
    )
