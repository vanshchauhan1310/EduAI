from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Enum as SAEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.session import Base


class InsightType(str, Enum):
    DROPOUT_RISK = "DROPOUT_RISK"
    ATTENDANCE_ANOMALY = "ATTENDANCE_ANOMALY"
    PERFORMANCE_DECLINE = "PERFORMANCE_DECLINE"
    SCHOOL_HEALTH = "SCHOOL_HEALTH"
    TEACHER_PERFORMANCE = "TEACHER_PERFORMANCE"
    ENROLLMENT_TREND = "ENROLLMENT_TREND"
    RECOMMENDATION = "RECOMMENDATION"


class InsightScope(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    SCHOOL = "SCHOOL"
    MANDAL = "MANDAL"
    DISTRICT = "DISTRICT"


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    insight_type: Mapped[InsightType] = mapped_column(SAEnum(InsightType), nullable=False, index=True)
    scope: Mapped[InsightScope] = mapped_column(SAEnum(InsightScope), nullable=False)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Scores
    risk_score: Mapped[float | None] = mapped_column(Float)        # 0.0 – 1.0
    confidence: Mapped[float | None] = mapped_column(Float)        # 0.0 – 1.0

    # Human-readable output
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_analysis: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)      # JSON list

    # Model metadata
    model_version: Mapped[str | None] = mapped_column(String(50))
    feature_values: Mapped[dict | None] = mapped_column(JSON)      # feature importance
    is_actioned: Mapped[bool] = mapped_column(String(1), default="0")
    actioned_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    action_notes: Mapped[str | None] = mapped_column(Text)

    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
