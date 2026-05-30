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
    Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
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
    school              = Column(String, nullable=True)
    language_preference = Column(String, default="both")   # english | telugu | both
    created_at          = Column(DateTime, default=datetime.utcnow)

    assessments  = relationship("Assessment",     back_populates="student")
    masteries    = relationship("ConceptMastery", back_populates="student")
    quiz_attempts = relationship("QuizAttempt",   back_populates="student")


# ── assessments ───────────────────────────────────────────────────────────────
class Assessment(Base):
    __tablename__ = "assessments"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id"))
    subject      = Column(String)
    chapter      = Column(String)
    scores       = Column(JSON)          # {concept: score, ...}
    total_marks  = Column(Integer, default=0)
    marks_scored = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="assessments")


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
    udise_code  = Column(String, unique=True, index=True, nullable=True)  # govt school id
    district    = Column(String, index=True)
    mandal      = Column(String, index=True)                              # MEO cluster
    address     = Column(Text, nullable=True)
    health_score = Column(Float, default=0.0)   # composite 0–100 (computed later)
    created_at  = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="school")


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

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    school_id  = Column(Integer, ForeignKey("schools.id"), index=True)
    date       = Column(String, index=True)          # YYYY-MM-DD
    status     = Column(String, default="present")   # present | absent | late
    marked_by  = Column(Integer, ForeignKey("users.id"))  # teacher/HM user id
    created_at = Column(DateTime, default=datetime.utcnow)
