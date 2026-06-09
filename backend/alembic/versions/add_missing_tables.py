"""add_missing_tables

Revision ID: add_missing_tables
Revises: 981229740f43
Create Date: 2026-06-09 00:00:00

Tables that were created via SQLAlchemy create_all() directly in MySQL but were
never included in the Alembic migration history.  This migration inserts them
between initial_tables and add_deo_copilot_columns so a fresh PostgreSQL / Supabase
database can be bootstrapped correctly with `alembic upgrade head`.

Note: risk_alerts and teacher_rationalization are created here WITHOUT the scan_id
and plan_id columns respectively — those FK columns are added by the next migration
(add_deo_copilot_columns) exactly as they were added in MySQL.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "add_missing_tables"
down_revision: Union[str, None] = "981229740f43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── risk_scans ──────────────────────────────────────────────────────────
    op.create_table(
        "risk_scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("critical_schools", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_risk_mandals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_analysis", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_scans_id", "risk_scans", ["id"], unique=False)
    op.create_index("ix_risk_scans_user_id", "risk_scans", ["user_id"], unique=False)
    op.create_index("ix_risk_scans_district_id", "risk_scans", ["district_id"], unique=False)

    # ── risk_alerts (WITHOUT scan_id — added by add_deo_copilot_columns) ───
    op.create_table(
        "risk_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("risk_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("entity_name", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_alerts_id", "risk_alerts", ["id"], unique=False)
    op.create_index("ix_risk_alerts_user_id", "risk_alerts", ["user_id"], unique=False)
    op.create_index("ix_risk_alerts_district_id", "risk_alerts", ["district_id"], unique=False)
    op.create_index("ix_risk_alerts_risk_type", "risk_alerts", ["risk_type"], unique=False)

    # ── teacher_rationalization_plans ────────────────────────────────────────
    op.create_table(
        "teacher_rationalization_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("total_surplus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_deficit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schools_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_recommendations", sa.Text(), nullable=False),
        sa.Column("plan_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teacher_rationalization_plans_id", "teacher_rationalization_plans", ["id"], unique=False)
    op.create_index("ix_teacher_rationalization_plans_user_id", "teacher_rationalization_plans", ["user_id"], unique=False)

    # ── teacher_rationalization (WITHOUT plan_id — added by add_deo_copilot_columns) ──
    op.create_table(
        "teacher_rationalization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("school_name", sa.String(255), nullable=True),
        sa.Column("enrollment", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_teachers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_teachers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shortage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("surplus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subject_gaps", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("ai_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teacher_rationalization_id", "teacher_rationalization", ["id"], unique=False)
    op.create_index("ix_teacher_rationalization_user_id", "teacher_rationalization", ["user_id"], unique=False)
    op.create_index("ix_teacher_rationalization_district_id", "teacher_rationalization", ["district_id"], unique=False)

    # ── district_briefs ──────────────────────────────────────────────────────
    op.create_table(
        "district_briefs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("brief_date", sa.String(20), nullable=False),
        sa.Column("total_schools", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_students", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_teachers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_mandals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_attendance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("teacher_vacancies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_risk_schools", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dropout_risk_schools", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_district_briefs_id", "district_briefs", ["id"], unique=False)
    op.create_index("ix_district_briefs_user_id", "district_briefs", ["user_id"], unique=False)
    op.create_index("ix_district_briefs_district_id", "district_briefs", ["district_id"], unique=False)

    # ── district_communications ──────────────────────────────────────────────
    op.create_table(
        "district_communications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("communication_type", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("target_audience", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_district_communications_id", "district_communications", ["id"], unique=False)
    op.create_index("ix_district_communications_user_id", "district_communications", ["user_id"], unique=False)

    # ── generated_school_health_analyses ────────────────────────────────────
    op.create_table(
        "generated_school_health_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mandal_id", sa.Integer(), nullable=False),
        sa.Column("mandal_name", sa.String(255), nullable=True),
        sa.Column("selected_school_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cluster_insights", sa.Text(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("concerns", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("action_plan", sa.JSON(), nullable=False),
        sa.Column("top_school", sa.String(500), nullable=True),
        sa.Column("most_at_risk_school", sa.String(500), nullable=True),
        sa.Column("school_breakdown", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_school_health_analyses_id", "generated_school_health_analyses", ["id"], unique=False)
    op.create_index("ix_generated_school_health_analyses_user_id", "generated_school_health_analyses", ["user_id"], unique=False)

    # ── generated_meo_reports ────────────────────────────────────────────────
    op.create_table(
        "generated_meo_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("mandal_id", sa.Integer(), nullable=False),
        sa.Column("mandal_name", sa.String(255), nullable=True),
        sa.Column("template_fields", sa.JSON(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mandal_id"], ["mandals.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_meo_reports_id", "generated_meo_reports", ["id"], unique=False)
    op.create_index("ix_generated_meo_reports_user_id", "generated_meo_reports", ["user_id"], unique=False)
    op.create_index("ix_generated_meo_reports_report_type", "generated_meo_reports", ["report_type"], unique=False)

    # ── career_recommendations ───────────────────────────────────────────────
    op.create_table(
        "career_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("survey_responses_json", sa.Text(), nullable=True),
        sa.Column("recommendation_json", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id"),
    )
    op.create_index("ix_career_recommendations_id", "career_recommendations", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("career_recommendations")
    op.drop_index("ix_generated_meo_reports_report_type", table_name="generated_meo_reports")
    op.drop_index("ix_generated_meo_reports_user_id", table_name="generated_meo_reports")
    op.drop_index("ix_generated_meo_reports_id", table_name="generated_meo_reports")
    op.drop_table("generated_meo_reports")
    op.drop_index("ix_generated_school_health_analyses_user_id", table_name="generated_school_health_analyses")
    op.drop_index("ix_generated_school_health_analyses_id", table_name="generated_school_health_analyses")
    op.drop_table("generated_school_health_analyses")
    op.drop_index("ix_district_communications_user_id", table_name="district_communications")
    op.drop_index("ix_district_communications_id", table_name="district_communications")
    op.drop_table("district_communications")
    op.drop_index("ix_district_briefs_district_id", table_name="district_briefs")
    op.drop_index("ix_district_briefs_user_id", table_name="district_briefs")
    op.drop_index("ix_district_briefs_id", table_name="district_briefs")
    op.drop_table("district_briefs")
    op.drop_index("ix_teacher_rationalization_district_id", table_name="teacher_rationalization")
    op.drop_index("ix_teacher_rationalization_user_id", table_name="teacher_rationalization")
    op.drop_index("ix_teacher_rationalization_id", table_name="teacher_rationalization")
    op.drop_table("teacher_rationalization")
    op.drop_index("ix_teacher_rationalization_plans_user_id", table_name="teacher_rationalization_plans")
    op.drop_index("ix_teacher_rationalization_plans_id", table_name="teacher_rationalization_plans")
    op.drop_table("teacher_rationalization_plans")
    op.drop_index("ix_risk_alerts_risk_type", table_name="risk_alerts")
    op.drop_index("ix_risk_alerts_district_id", table_name="risk_alerts")
    op.drop_index("ix_risk_alerts_user_id", table_name="risk_alerts")
    op.drop_index("ix_risk_alerts_id", table_name="risk_alerts")
    op.drop_table("risk_alerts")
    op.drop_index("ix_risk_scans_district_id", table_name="risk_scans")
    op.drop_index("ix_risk_scans_user_id", table_name="risk_scans")
    op.drop_index("ix_risk_scans_id", table_name="risk_scans")
    op.drop_table("risk_scans")
