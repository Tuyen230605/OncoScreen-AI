"""init schema - create all 5 core tables.

Revision ID: e4ae8d137edf
Revises:
Create Date: 2026-09-30 19:03:57.459590

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4ae8d137edf'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. patient_profiles
    op.create_table(
        'patient_profiles',
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(length=16), nullable=False),
        sa.Column('genetics_history', sa.JSON(), nullable=False),
        sa.Column('lifestyle', sa.JSON(), nullable=False),
        sa.Column('lifestyle_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # 3. screening_sessions
    op.create_table(
        'screening_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('questionnaire', sa.JSON(), nullable=True),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('red_flags', sa.JSON(), nullable=True),
        sa.Column('risk_assessment', sa.JSON(), nullable=True),
        sa.Column('draft_plan', sa.JSON(), nullable=True),
        sa.Column('final_plan', sa.JSON(), nullable=True),
        sa.Column('doctor_note', sa.Text(), nullable=True),
        sa.Column('trace_id', sa.String(length=64), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_screening_sessions_patient_id'), 'screening_sessions', ['patient_id'], unique=False)
    op.create_index(op.f('ix_screening_sessions_status'), 'screening_sessions', ['status'], unique=False)

    # 4. reminders
    op.create_table(
        'reminders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('cancer_type', sa.String(length=32), nullable=False),
        sa.Column('method', sa.String(length=255), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.ForeignKeyConstraint(['session_id'], ['screening_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reminders_due_date'), 'reminders', ['due_date'], unique=False)
    op.create_index(op.f('ix_reminders_patient_id'), 'reminders', ['patient_id'], unique=False)

    # 5. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['session_id'], ['screening_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_reminders_patient_id'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_due_date'), table_name='reminders')
    op.drop_table('reminders')
    op.drop_index(op.f('ix_screening_sessions_status'), table_name='screening_sessions')
    op.drop_index(op.f('ix_screening_sessions_patient_id'), table_name='screening_sessions')
    op.drop_table('screening_sessions')
    op.drop_table('patient_profiles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
