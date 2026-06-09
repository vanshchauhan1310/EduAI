from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.session import Base

# Starting mastery for a concept the learner has never attempted (0-100 scale).
DEFAULT_MASTERY = 20.0


class ConceptMastery(Base):
    """Per-student, per-concept mastery score (0-100) — server-authoritative source
    for /tutor/mastery* and the EMA update applied after each graded quiz."""

    __tablename__ = "tutor_concept_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "subject", "chapter", "concept", name="uq_tutor_mastery_concept"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter: Mapped[str] = mapped_column(String(255), nullable=False)
    concept: Mapped[str] = mapped_column(String(255), nullable=False)
    mastery: Mapped[float] = mapped_column(Float, nullable=False, default=DEFAULT_MASTERY)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class TutorKnowledgeChunk(Base):
    """A chunk of ingested-PDF text indexed by the RAG retriever.

    `student_id IS NULL` rows are shared/seeded sources (e.g. NCERT chapters
    ingested by the seed script) visible to every student; non-null rows are a
    student's own "My Study Material" uploads, private to them.
    """

    __tablename__ = "tutor_knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
