"""add chapter memories

Revision ID: 0018_add_chapter_memories
Revises: 0017_add_world_truth_layers
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0018_add_chapter_memories'
down_revision: str | None = '0017_add_world_truth_layers'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'chapter_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('emotional_arc', sa.Text(), nullable=False),
        sa.Column('causal_links', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('characters_present', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chapter_id', name='uq_chapter_memory_chapter'),
    )
    op.create_index('ix_chapter_memories_chapter_id', 'chapter_memories', ['chapter_id'])
    op.create_index('ix_chapter_memories_world_id', 'chapter_memories', ['world_id'])


def downgrade() -> None:
    op.drop_table('chapter_memories')
