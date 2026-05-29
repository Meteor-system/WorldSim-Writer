"""add world story arc

Revision ID: 0006_add_world_story_arc
Revises: 0005_add_foreshadow_events
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0006_add_world_story_arc'
down_revision: str | None = '0005_add_foreshadow_events'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'worlds',
        sa.Column(
            'story_arc',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('worlds', 'story_arc')
