from datetime import date, datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class AssessmentType(str, Enum):
    FORMATIVE = "FORMATIVE"
    SUMMATIVE = "SUMMATIVE"
    UNIT_TEST = "UNIT_TEST"
    HALF_YEARLY = "HALF_YEARLY"
    ANNUAL = "ANNUAL"
    SA1 = "SA1"
    SA2 = "SA2"
    FA1 = "FA1"
    FA2 = "FA2"
    FA3 = "FA3"
    FA4 = "FA4"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    assessment_type: Mapped[AssessmentType] = mapped_column(SAEnum(AssessmentType), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    class_grade: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String(5))
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)

    scheduled_date: Mapped[date | None] = mapped_column(Date)
    conducted_date: Mapped[date | None] = mapped_column(Date)
    max_marks: Mapped[float] = mapped_column(Float, nullable=False)
    passing_marks: Mapped[float | None] = mapped_column(Float)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    results: Mapped[list["AssessmentResult"]] = relationship("AssessmentResult", back_populates="assessment")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(Integer, ForeignKey("assessments.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)

    marks_obtained: Mapped[float | None] = mapped_column(Float)
    grade: Mapped[str | None] = mapped_column(String(5))  # A+/A/B/C/D/F
    percentage: Mapped[float | None] = mapped_column(Float)
    rank_in_class: Mapped[int | None] = mapped_column(Integer)

    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    teacher_feedback: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    assessment: Mapped[Assessment] = relationship("Assessment", back_populates="results")
    student: Mapped["Student"] = relationship("Student", back_populates="assessment_results")
