"""Add student_ml_input and student_predictions tables

Revision ID: add_student_ml_tables
Revises: add_deo_copilot_columns
Create Date: 2026-06-01 00:20:00

Dropout Prediction 2-Table Architecture:
  - student_ml_input (stores 20 model input features per student)
  - student_predictions (stores model output — JOIN with students for names)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "add_student_ml_tables"
down_revision: Union[str, None] = "add_deo_copilot_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── student_ml_input table ──
    op.create_table(
        "student_ml_input",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False, server_default="Male"),
        sa.Column("class_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("age", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("guardian_education", sa.String(20), nullable=False, server_default="Secondary"),
        sa.Column("health_risk", sa.String(10), nullable=False, server_default="Low"),
        sa.Column("attendance_pct", sa.Float(), nullable=False, server_default="90.0"),
        sa.Column("avg_marks", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("family_income_monthly", sa.Float(), nullable=False, server_default="12000.0"),
        sa.Column("distance_to_school_km", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("study_hours_per_day", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("school_engagement_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("teacher_feedback_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("previous_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disciplinary_incidents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("single_parent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sibling_dropout", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mobile_available", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("internet_access", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scholarship", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("midday_meal", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_ml_input_student", "student_ml_input", ["student_id"], unique=False)

    # ── student_predictions table ──
    op.create_table(
        "student_predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("dropout_probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("predicted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("batch_id", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_student_predictions_student_risk", "student_predictions", ["student_id", "risk_level"], unique=False)
    op.create_index("ix_student_predictions_predicted_at", "student_predictions", ["predicted_at"], unique=False)
    op.create_index("ix_student_predictions_batch", "student_predictions", ["batch_id"], unique=False)


def downgrade() -> None:
    op.drop_table("student_predictions")
    op.drop_table("student_ml_input")