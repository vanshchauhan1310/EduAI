from datetime import date, datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, Enum as SAEnum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admission_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    aadhaar_no: Mapped[str | None] = mapped_column(String(12), unique=True, index=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender), nullable=False)
    category: Mapped[str | None] = mapped_column(String(20))  # SC/ST/OBC/General

    # Parent info
    parent_name: Mapped[str | None] = mapped_column(String(255))
    parent_phone: Mapped[str | None] = mapped_column(String(20), index=True)
    parent_email: Mapped[str | None] = mapped_column(String(255))

    # Academic
    current_class: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–12
    section: Mapped[str | None] = mapped_column(String(5))  # A/B/C
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)  # "2024-25"
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"), nullable=False)

    # User account (optional — if student has login)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))

    # Social welfare
    receives_midday_meal: Mapped[bool] = mapped_column(Boolean, default=True)
    receives_scholarship: Mapped[bool] = mapped_column(Boolean, default=False)
    has_disability: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI Risk
    dropout_risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[RiskLevel] = mapped_column(SAEnum(RiskLevel), default=RiskLevel.LOW)
    risk_factors: Mapped[str | None] = mapped_column(Text)  # JSON string
    risk_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    enrollment_date: Mapped[date | None] = mapped_column(Date)
    dropout_date: Mapped[date | None] = mapped_column(Date)
    dropout_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    school: Mapped["School"] = relationship("School", back_populates="students")
    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    assessment_results: Mapped[list["AssessmentResult"]] = relationship("AssessmentResult", back_populates="student")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
