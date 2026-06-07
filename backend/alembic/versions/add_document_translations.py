"""add_document_translations

Revision ID: add_document_translations
Revises: add_student_ml_tables
Create Date: 2026-06-07 18:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "add_document_translations"
down_revision: Union[str, None] = "add_student_ml_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("source_language", sa.String(length=50), nullable=False),
        sa.Column("target_language", sa.String(length=50), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("original_length", sa.Integer(), nullable=True),
        sa.Column("translated_length", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_translations_id"), "document_translations", ["id"], unique=False)
    op.create_index(op.f("ix_document_translations_user_id"), "document_translations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_translations_user_id"), table_name="document_translations")
    op.drop_index(op.f("ix_document_translations_id"), table_name="document_translations")
    op.drop_table("document_translations")
