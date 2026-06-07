"""
StudentMLInput — Stores model-ready features for each student.

This table holds the 20 engineered features that the XGBoost pipeline
consumes. The feature_builder computes these once and persists them,
so predictions can be re-run without re-fetching attendance/assessments.

Separating input from students table keeps the student schema clean
and avoids polluting it with ML-specific columns.
"""

from datetime import datetime
from sqlalchemy import (
    Integer,
    Float,
    String,
    ForeignKey,
    DateTime,
    Text,
    Index,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class StudentMLInput(Base):
    __tablename__ = "student_ml_input"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ─── 20 Model Features ─────────────────────────────────────
    # Categorical
    gender: Mapped[str] = mapped_column(String(10), nullable=False, default="Male")
    class_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    guardian_education: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Secondary"
    )
    health_risk: Mapped[str] = mapped_column(
        String(10), nullable=False, default="Low"
    )

    # Numeric continuous
    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=90.0)
    avg_marks: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    family_income_monthly: Mapped[float] = mapped_column(
        Float, nullable=False, default=12000.0
    )
    distance_to_school_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=2.5
    )
    study_hours_per_day: Mapped[float] = mapped_column(
        Float, nullable=False, default=2.0
    )
    school_engagement_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )
    teacher_feedback_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )

    # Discrete counts
    previous_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    disciplinary_incidents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Binary flags
    single_parent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sibling_dropout: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mobile_available: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    internet_access: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scholarship: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    midday_meal: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    student: Mapped["Student"] = relationship("Student", backref="ml_input")

    __table_args__ = (
        Index("ix_ml_input_student", "student_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentMLInput student_id={self.student_id} "
            f"class_level={self.class_level} attendance={self.attendance_pct}>"
        )