"""add world snapshots

Revision ID: 0010_add_world_snapshots
Revises: 0009_add_character_arc_report
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0010_add_world_snapshots'
down_revision: str | None = '0009_add_character_arc_report'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'world_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('world_version', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=160), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_world_snapshots_world_id'), 'world_snapshots', ['world_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_world_snapshots_world_id'), table_name='world_snapshots')
    op.drop_table('world_snapshots')
