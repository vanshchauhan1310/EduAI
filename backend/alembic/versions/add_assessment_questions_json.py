"""add_assessment_questions_json

Revision ID: add_assessment_questions_json
Revises: add_document_translations
Create Date: 2026-06-08 01:15:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "add_assessment_questions_json"
down_revision: Union[str, None] = "add_document_translations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("questions_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessments", "questions_json")
