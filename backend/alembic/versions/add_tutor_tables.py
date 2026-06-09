"""add_tutor_tables

Revision ID: add_tutor_tables
Revises: add_assessment_questions_json
Create Date: 2026-06-08 02:00:00

AI Tutor (student portal) backend tables:
  - tutor_concept_mastery  (per-student, per-concept mastery score 0-100)
  - tutor_knowledge_chunks (RAG corpus: shared/seeded + per-student "My Study Material")
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "add_tutor_tables"
down_revision: Union[str, None] = "add_assessment_questions_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutor_concept_mastery",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("chapter", sa.String(255), nullable=False),
        sa.Column("concept", sa.String(255), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False, server_default="20.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subject", "chapter", "concept", name="uq_tutor_mastery_concept"),
    )
    op.create_index("ix_tutor_mastery_student", "tutor_concept_mastery", ["student_id"], unique=False)

    op.create_table(
        "tutor_knowledge_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("chapter", sa.String(255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tutor_chunks_student", "tutor_knowledge_chunks", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_table("tutor_knowledge_chunks")
    op.drop_table("tutor_concept_mastery")
