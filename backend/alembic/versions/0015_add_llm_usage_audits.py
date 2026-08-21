"""add llm usage audits

Revision ID: 0015_add_llm_usage_audits
Revises: 0014_add_chapter_draft_quality_report
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0015_add_llm_usage_audits'
down_revision: str | None = '0014_add_chapter_draft_quality_report'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'llm_usage_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('draft_id', sa.Integer(), nullable=True),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('api_mode', sa.String(length=40), nullable=False),
        sa.Column('model', sa.String(length=200), nullable=False),
        sa.Column('is_mock', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('schema_fallback_used', sa.Boolean(), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('input_message_count', sa.Integer(), nullable=False),
        sa.Column('input_chars', sa.Integer(), nullable=False),
        sa.Column('output_chars', sa.Integer(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(length=40), nullable=True),
        sa.Column('request_id', sa.String(length=200), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['draft_id'], ['chapter_drafts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_llm_usage_audits_world_id'), 'llm_usage_audits', ['world_id'], unique=False)
    op.create_index(op.f('ix_llm_usage_audits_chapter_id'), 'llm_usage_audits', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_llm_usage_audits_draft_id'), 'llm_usage_audits', ['draft_id'], unique=False)
    op.create_index(op.f('ix_llm_usage_audits_operation'), 'llm_usage_audits', ['operation'], unique=False)
    op.create_index(op.f('ix_llm_usage_audits_status'), 'llm_usage_audits', ['status'], unique=False)
    op.create_index(op.f('ix_llm_usage_audits_created_at'), 'llm_usage_audits', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_llm_usage_audits_created_at'), table_name='llm_usage_audits')
    op.drop_index(op.f('ix_llm_usage_audits_status'), table_name='llm_usage_audits')
    op.drop_index(op.f('ix_llm_usage_audits_operation'), table_name='llm_usage_audits')
    op.drop_index(op.f('ix_llm_usage_audits_draft_id'), table_name='llm_usage_audits')
    op.drop_index(op.f('ix_llm_usage_audits_chapter_id'), table_name='llm_usage_audits')
    op.drop_index(op.f('ix_llm_usage_audits_world_id'), table_name='llm_usage_audits')
    op.drop_table('llm_usage_audits')
