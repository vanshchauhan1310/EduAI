"""
Database Models (SQLAlchemy ORM)
================================
Six tables that store everything EduSakhi needs:

    students         → student profile
    assessments      → diagnostic test results
    concept_mastery  → per-concept mastery score (0.0–1.0)
    learning_paths   → generated adaptive paths
    quiz_attempts    → quiz history
    analytics        → aggregated running totals
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship

from database.db import Base


# ── students ──────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String, nullable=False)
    age                 = Column(Integer, nullable=True)
    grade               = Column(String, default="10")
    school              = Column(String, nullable=True)            # legacy free-text
    language_preference = Column(String, default="both")   # english | telugu | both
    created_at          = Column(DateTime, default=datetime.utcnow)

    # ── governance fields (architecture-aligned) ──────────────────────────────
    school_id           = Column(Integer, ForeignKey("schools.id"), index=True, nullable=True)
    admission_no        = Column(String, index=True, nullable=True)
    risk_level          = Column(String, default="LOW")            # LOW|MEDIUM|HIGH|CRITICAL
    dropout_risk_score  = Column(Float, default=0.0)               # 0.0 – 1.0
    is_active           = Column(Integer, default=1)

    masteries     = relationship("ConceptMastery", back_populates="student")
    quiz_attempts = relationship("QuizAttempt",   back_populates="student")
    results       = relationship("AssessmentResult", back_populates="student")

    __table_args__ = (Index("idx_students_school_risk", "school_id", "risk_level"),)


# ── assessments (school exams — architecture-aligned) ──────────────────────────
class Assessment(Base):
    __tablename__ = "assessments"

    id              = Column(Integer, primary_key=True, index=True)
    school_id       = Column(Integer, ForeignKey("schools.id"), index=True)
    class_grade     = Column(String, index=True)        # e.g. "10"
    assessment_type = Column(String)                    # FA1 | SA1 | Unit Test | ...
    subject         = Column(String)
    max_marks       = Column(Integer, default=100)
    date            = Column(String)                    # YYYY-MM-DD
    created_at      = Column(DateTime, default=datetime.utcnow)

    results = relationship("AssessmentResult", back_populates="assessment")


# ── assessment_results ─────────────────────────────────────────────────────────
class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id             = Column(Integer, primary_key=True, index=True)
    assessment_id  = Column(Integer, ForeignKey("assessments.id"), index=True)
    student_id     = Column(Integer, ForeignKey("students.id"), index=True)
    marks_obtained = Column(Float, default=0.0)
    percentage     = Column(Float, default=0.0)
    grade          = Column(String, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="results")
    student    = relationship("Student",    back_populates="results")


# ── concept_mastery ───────────────────────────────────────────────────────────
class ConceptMastery(Base):
    __tablename__ = "concept_mastery"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(Integer, ForeignKey("students.id"))
    concept       = Column(String, index=True)
    subject       = Column(String)
    chapter       = Column(String)
    mastery_score = Column(Float, default=0.0)   # 0.0 – 1.0
    attempts      = Column(Integer, default=0)
    last_updated  = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="masteries")


# ── learning_paths ────────────────────────────────────────────────────────────
class LearningPath(Base):
    __tablename__ = "learning_paths"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"))
    subject      = Column(String)
    chapter      = Column(String)
    path_data    = Column(JSON)          # full path dict
    generated_at = Column(DateTime, default=datetime.utcnow)


# ── quiz_attempts ─────────────────────────────────────────────────────────────
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"))
    subject      = Column(String)
    chapter      = Column(String)
    concept      = Column(String)
    difficulty   = Column(String)
    score        = Column(Float, default=0.0)    # 0.0 – 1.0
    time_spent   = Column(Integer, default=0)    # seconds
    quiz_data    = Column(JSON)          # the questions
    answers      = Column(JSON)          # student answers
    attempted_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="quiz_attempts")


# ── analytics ─────────────────────────────────────────────────────────────────
class Analytics(Base):
    __tablename__ = "analytics"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"))
    concept      = Column(String)
    subject      = Column(String)
    mastery      = Column(Float, default=0.0)
    attempts     = Column(Integer, default=0)
    score        = Column(Float, default=0.0)
    time_spent   = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE LAYER (integrated with EduSakhi — same Base, same database)
# ══════════════════════════════════════════════════════════════════════════════

# ── schools ───────────────────────────────────────────────────────────────────
class School(Base):
    __tablename__ = "schools"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    dise_code   = Column(String, unique=True, index=True, nullable=True)  # govt school id
    udise_code  = Column(String, index=True, nullable=True)               # legacy alias
    district    = Column(String, index=True)                              # legacy free-text
    mandal      = Column(String, index=True)                              # legacy free-text
    district_id = Column(Integer, ForeignKey("districts.id"), index=True, nullable=True)
    mandal_id   = Column(Integer, ForeignKey("mandals.id"), index=True, nullable=True)
    address     = Column(Text, nullable=True)
    health_score = Column(Float, default=0.0)   # composite 0–100 (computed later)
    created_at  = Column(DateTime, default=datetime.utcnow)

    users    = relationship("User", back_populates="school")
    teachers = relationship("Teacher", back_populates="school")


# ── users (auth + roles) ──────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role            = Column(String, nullable=False, index=True)   # core.roles.Role value
    is_active       = Column(Integer, default=1)                   # 1 = active, 0 = disabled
    school_id       = Column(Integer, ForeignKey("schools.id"), nullable=True)
    # Links a STUDENT/PARENT user to their EduSakhi learning profile.
    student_id      = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="users")


# ── attendance ────────────────────────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    id             = Column(Integer, primary_key=True, index=True)
    student_id     = Column(Integer, ForeignKey("students.id"), index=True)
    school_id      = Column(Integer, ForeignKey("schools.id"), index=True)
    # Polymorphic reference (architecture): STUDENT | TEACHER. student_id kept for
    # backward compatibility with existing attendance routes.
    reference_type = Column(String, default="STUDENT")
    reference_id   = Column(Integer, index=True, nullable=True)
    date           = Column(String, index=True)          # YYYY-MM-DD
    status         = Column(String, default="present")   # present | absent | late
    marked_by      = Column(Integer, ForeignKey("users.id"))  # teacher/HM user id
    created_at     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_attendance_school_date", "school_id", "date"),)


# ══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE HIERARCHY + AI/NOTIFICATIONS (architecture-aligned tables)
# ══════════════════════════════════════════════════════════════════════════════

# ── districts ───────────────────────────────────────────────────────────────────
class District(Base):
    __tablename__ = "districts"

    id    = Column(Integer, primary_key=True, index=True)
    name  = Column(String, unique=True, index=True, nullable=False)
    state = Column(String, nullable=True)

    mandals = relationship("Mandal", back_populates="district")


# ── mandals (MEO clusters) ──────────────────────────────────────────────────────
class Mandal(Base):
    __tablename__ = "mandals"

    id          = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), index=True)
    name        = Column(String, nullable=False)

    district = relationship("District", back_populates="mandals")


# ── teachers ────────────────────────────────────────────────────────────────────
class Teacher(Base):
    __tablename__ = "teachers"

    id           = Column(Integer, primary_key=True, index=True)
    employee_id  = Column(String, unique=True, index=True, nullable=True)
    school_id    = Column(Integer, ForeignKey("schools.id"), index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    name         = Column(String, nullable=False)
    subject_area = Column(String, nullable=True)
    teacher_type = Column(String, nullable=True)   # regular | contract | guest
    created_at   = Column(DateTime, default=datetime.utcnow)

    school = relationship("School", back_populates="teachers")


# ── notifications ───────────────────────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id           = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True)
    channel      = Column(String, default="IN_APP")   # PUSH | WHATSAPP | SMS | IN_APP
    title        = Column(String, nullable=True)
    body         = Column(Text, nullable=True)
    status       = Column(String, default="PENDING")  # PENDING|SENT|DELIVERED|READ|FAILED
    is_read      = Column(Integer, default=0)
    created_at   = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_notifications_recipient", "recipient_id", "is_read", "created_at"),
    )


# ── ai_insights (polymorphic: STUDENT | SCHOOL | MANDAL | DISTRICT) ─────────────
class AIInsight(Base):
    __tablename__ = "ai_insights"

    id           = Column(Integer, primary_key=True, index=True)
    scope        = Column(String, index=True)     # STUDENT | SCHOOL | MANDAL | DISTRICT
    insight_type = Column(String)                 # dropout_risk | school_health | ...
    reference_id = Column(Integer, index=True)    # id of the scoped entity
    risk_score   = Column(Float, default=0.0)     # 0.0 – 1.0
    risk_level   = Column(String, nullable=True)  # LOW|MEDIUM|HIGH|CRITICAL
    summary      = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_insights_scope_ref", "scope", "reference_id"),)
