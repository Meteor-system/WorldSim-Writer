"""add character arc report

Revision ID: 0009_add_character_arc_report
Revises: 0008_add_draft_version_metadata
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0009_add_character_arc_report'
down_revision: str | None = '0008_add_draft_version_metadata'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('chapters', sa.Column('character_arc_report', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.alter_column('chapters', 'character_arc_report', server_default=None)


def downgrade() -> None:
    op.drop_column('chapters', 'character_arc_report')
