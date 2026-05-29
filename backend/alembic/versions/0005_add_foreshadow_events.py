"""add foreshadow events

Revision ID: 0005_add_foreshadow_events
Revises: 0004_add_state_consistency_foundation
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005_add_foreshadow_events'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'foreshadow_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('foreshadow_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['foreshadow_id'], ['foreshadows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_foreshadow_events_chapter_id'), 'foreshadow_events', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_foreshadow_events_foreshadow_id'), 'foreshadow_events', ['foreshadow_id'], unique=False)
    op.create_index('ix_foreshadow_events_foreshadow_created', 'foreshadow_events', ['foreshadow_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_foreshadow_events_foreshadow_created', table_name='foreshadow_events')
    op.drop_index(op.f('ix_foreshadow_events_foreshadow_id'), table_name='foreshadow_events')
    op.drop_index(op.f('ix_foreshadow_events_chapter_id'), table_name='foreshadow_events')
    op.drop_table('foreshadow_events')
