"""
StudentPrediction — Stores ML model prediction outputs for each student.

This table holds the output from the XGBoost dropout prediction model.
Each row is linked to a student via student_id, and student name/admission_no
is retrieved by JOINing with the students table.

Dashboard queries (HM/MEO/DEO) JOIN this table with students + schools
to present enriched results.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class StudentPrediction(Base):
    __tablename__ = "student_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Prediction outputs from ML model
    dropout_probability: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Probability score 0-100"
    )
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Low / Medium / High / Critical"
    )
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    model_version: Mapped[str | None] = mapped_column(String(50))
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Batch tracking
    batch_id: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        comment="Groups predictions run together (e.g. daily cron batch)",
    )

    # Relationship — JOIN with students table to get name/admission_no
    student: Mapped["Student"] = relationship("Student", backref="predictions")

    __table_args__ = (
        Index("ix_student_predictions_student_risk", "student_id", "risk_level"),
        Index("ix_student_predictions_predicted_at", "predicted_at"),
        Index("ix_student_predictions_batch", "batch_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentPrediction student_id={self.student_id} "
            f"risk_level={self.risk_level} probability={self.dropout_probability}>"
        )