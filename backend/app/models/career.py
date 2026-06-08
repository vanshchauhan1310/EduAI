from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.session import Base


class CareerRecommendation(Base):
    """
    One row per student — holds their aptitude/interest survey responses and the
    latest AI-generated career & skill recommendation derived from those responses
    plus their real academic performance and attendance signals.
    """
    __tablename__ = "career_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), unique=True, nullable=False)

    survey_responses_json: Mapped[str | None] = mapped_column(Text)  # [{question_id, answer}]
    recommendation_json: Mapped[str | None] = mapped_column(Text)    # structured AI output
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
