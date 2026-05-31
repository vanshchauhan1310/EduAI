"""
DEO Copilot Models - District Intelligence, Risk Monitoring,
Teacher Rationalization, and Governance Communications.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.session import Base


class DistrictBrief(Base):
    """AI-generated daily district intelligence brief."""
    __tablename__ = "district_briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    brief_date: Mapped[str] = mapped_column(String(20), nullable=False)
    total_schools: Mapped[int] = mapped_column(Integer, default=0)
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    total_teachers: Mapped[int] = mapped_column(Integer, default=0)
    active_mandals: Mapped[int] = mapped_column(Integer, default=0)
    avg_attendance: Mapped[float] = mapped_column(Float, default=0.0)
    teacher_vacancies: Mapped[int] = mapped_column(Integer, default=0)
    high_risk_schools: Mapped[int] = mapped_column(Integer, default=0)
    dropout_risk_schools: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskScan(Base):
    """District risk scan records."""
    __tablename__ = "risk_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    critical_schools: Mapped[int] = mapped_column(Integer, default=0)
    high_risk_mandals: Mapped[int] = mapped_column(Integer, default=0)
    ai_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskAlert(Base):
    """District-level risk alerts and escalations."""
    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    scan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("risk_scans.id"))
    risk_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    entity_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_resolved: Mapped[bool] = mapped_column(default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeacherRationalizationPlan(Base):
    """Summary record for teacher rationalization analysis."""
    __tablename__ = "teacher_rationalization_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    total_surplus: Mapped[int] = mapped_column(Integer, default=0)
    total_deficit: Mapped[int] = mapped_column(Integer, default=0)
    schools_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    ai_recommendations: Mapped[str] = mapped_column(Text, nullable=False)
    plan_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeacherRationalization(Base):
    """Teacher deployment and rationalization records per school."""
    __tablename__ = "teacher_rationalization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teacher_rationalization_plans.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    school_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("schools.id"))
    school_name: Mapped[str | None] = mapped_column(String(255))
    enrollment: Mapped[int] = mapped_column(Integer, default=0)
    current_teachers: Mapped[int] = mapped_column(Integer, default=0)
    required_teachers: Mapped[int] = mapped_column(Integer, default=0)
    shortage: Mapped[int] = mapped_column(Integer, default=0)
    surplus: Mapped[int] = mapped_column(Integer, default=0)
    subject_gaps: Mapped[list | None] = mapped_column(JSON)
    recommendations: Mapped[list | None] = mapped_column(JSON)
    ai_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DistrictCommunication(Base):
    """District-level official communications."""
    __tablename__ = "district_communications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    communication_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())