"""
SQL persistence for the prototype (SQLite via SQLAlchemy)
========================================================
Stores learners, their per-topic mastery, and every quiz attempt, so progress
survives across runs. Self-contained — uses its own prototype.db file.

Tables:
    learners       (id, name)
    progress       (id, learner_id, topic, mastery, updated_at)   one row per learner+topic
    quiz_attempts  (id, learner_id, topic, difficulty, correct, total, score, created_at)
"""

import os
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DB_PATH = os.getenv("PROTOTYPE_DB", "sqlite:///./prototype.db")

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Starting mastery for a learner who has never seen a topic (0-100 scale).
DEFAULT_MASTERY = 20.0


# ── Models ────────────────────────────────────────────────────────────────────
class Learner(Base):
    __tablename__ = "learners"
    id   = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Progress(Base):
    __tablename__ = "progress"
    id         = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), index=True)
    topic      = Column(String, index=True)
    mastery    = Column(Float, default=DEFAULT_MASTERY)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("learner_id", "topic", name="uq_learner_topic"),)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id         = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), index=True)
    topic      = Column(String)
    difficulty = Column(String)
    correct    = Column(Integer)
    total      = Column(Integer)
    score      = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class KBChunk(Base):
    """A chunk of text parsed from an uploaded PDF — the RAG knowledge base."""
    __tablename__ = "kb_chunks"
    id         = Column(Integer, primary_key=True)
    source     = Column(String, index=True)   # pdf filename
    page       = Column(Integer)
    subject    = Column(String, index=True)
    chapter    = Column(String, index=True)
    text       = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


# ── Helper operations ─────────────────────────────────────────────────────────
def get_or_create_learner(db: Session, name: str) -> Learner:
    learner = db.query(Learner).filter(Learner.name == name).first()
    if not learner:
        learner = Learner(name=name)
        db.add(learner)
        db.commit()
        db.refresh(learner)
    return learner


def get_mastery(db: Session, learner_id: int, topic: str) -> float:
    row = (
        db.query(Progress)
        .filter(Progress.learner_id == learner_id, Progress.topic == topic)
        .first()
    )
    return row.mastery if row else DEFAULT_MASTERY


def set_mastery(db: Session, learner_id: int, topic: str, mastery: float) -> None:
    row = (
        db.query(Progress)
        .filter(Progress.learner_id == learner_id, Progress.topic == topic)
        .first()
    )
    if row:
        row.mastery = mastery
        row.updated_at = datetime.utcnow()
    else:
        db.add(Progress(learner_id=learner_id, topic=topic, mastery=mastery))
    db.commit()


def record_attempt(
    db: Session, learner_id: int, topic: str, difficulty: str,
    correct: int, total: int, score: float,
) -> None:
    db.add(QuizAttempt(
        learner_id=learner_id, topic=topic, difficulty=difficulty,
        correct=correct, total=total, score=score,
    ))
    db.commit()


def get_history(db: Session, learner_id: int, topic: str):
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.learner_id == learner_id, QuizAttempt.topic == topic)
        .order_by(QuizAttempt.created_at)
        .all()
    )


# ── Knowledge base (PDF chunks) ────────────────────────────────────────────────
def add_chunks(db: Session, source: str, subject: str, chapter: str,
               chunks: list) -> int:
    """chunks: list of (page:int, text:str). Returns number stored."""
    for page, text in chunks:
        db.add(KBChunk(source=source, page=page, subject=subject,
                       chapter=chapter, text=text))
    db.commit()
    return len(chunks)


def all_chunks(db: Session):
    return db.query(KBChunk).all()


def count_chunks(db: Session) -> int:
    return db.query(KBChunk).count()


def count_chunks_for(db: Session, subject: str, chapter: str) -> int:
    return (
        db.query(KBChunk)
        .filter(KBChunk.subject == subject, KBChunk.chapter == chapter)
        .count()
    )


def kb_sources(db: Session):
    """Return [(source, subject, chapter, n_chunks)] grouped by file."""
    from sqlalchemy import func
    return (
        db.query(KBChunk.source, KBChunk.subject, KBChunk.chapter,
                 func.count(KBChunk.id))
        .group_by(KBChunk.source, KBChunk.subject, KBChunk.chapter)
        .all()
    )


def delete_all_chunks(db: Session) -> int:
    n = db.query(KBChunk).delete()
    db.commit()
    return n
