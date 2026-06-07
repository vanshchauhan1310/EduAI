"""add_deo_copilot_columns

Revision ID: add_deo_copilot_columns
Revises: 981229740f43
Create Date: 2026-05-31 18:47:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'add_deo_copilot_columns'
down_revision: Union[str, None] = '981229740f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scan_id column to risk_alerts table
    op.add_column('risk_alerts', sa.Column('scan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_risk_alerts_scan_id', 'risk_alerts', 'risk_scans', ['scan_id'], ['id'])

    # Add plan_id column to teacher_rationalization table
    op.add_column('teacher_rationalization', sa.Column('plan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_teacher_rationalization_plan_id', 'teacher_rationalization', 'teacher_rationalization_plans', ['plan_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_teacher_rationalization_plan_id', 'teacher_rationalization', type_='foreignkey')
    op.drop_column('teacher_rationalization', 'plan_id')

    op.drop_constraint('fk_risk_alerts_scan_id', 'risk_alerts', type_='foreignkey')
    op.drop_column('risk_alerts', 'scan_id')