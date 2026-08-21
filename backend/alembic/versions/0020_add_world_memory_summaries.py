"""add world memory summaries

Revision ID: 0020_add_world_memory_summaries
Revises: 0019_add_chapter_draft_memory_card
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0020_add_world_memory_summaries'
down_revision: str | None = '0019_add_chapter_draft_memory_card'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'world_memory_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('chapter_start', sa.Integer(), nullable=False),
        sa.Column('chapter_end', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_facts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('open_threads', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_world_memory_summaries_world_id', 'world_memory_summaries', ['world_id'])


def downgrade() -> None:
    op.drop_table('world_memory_summaries')
