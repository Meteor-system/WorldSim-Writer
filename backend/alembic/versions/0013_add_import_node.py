"""add import node

Revision ID: 0013_add_import_node
Revises: 0012_add_tags
Create Date: 2026-06-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0013_add_import_node'
down_revision: str | None = '0012_add_tags'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'import_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=40), nullable=False),
        sa.Column('source_title', sa.String(length=200), nullable=False),
        sa.Column('original_excerpt', sa.Text(), nullable=False),
        sa.Column('cleaned_excerpt', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('asset_counts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('conflicts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_import_batches_world_id'), 'import_batches', ['world_id'], unique=False)
    op.create_table(
        'import_candidate_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('asset_pool', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['import_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_import_candidate_assets_batch_id'), 'import_candidate_assets', ['batch_id'], unique=False)
    op.create_index(op.f('ix_import_candidate_assets_world_id'), 'import_candidate_assets', ['world_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_import_candidate_assets_world_id'), table_name='import_candidate_assets')
    op.drop_index(op.f('ix_import_candidate_assets_batch_id'), table_name='import_candidate_assets')
    op.drop_table('import_candidate_assets')
    op.drop_index(op.f('ix_import_batches_world_id'), table_name='import_batches')
    op.drop_table('import_batches')
