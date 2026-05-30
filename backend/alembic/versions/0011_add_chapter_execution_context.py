"""add chapter execution context

Revision ID: 0011_add_chapter_execution_context
Revises: 0010_add_world_snapshots
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0011_add_chapter_execution_context'
down_revision: str | None = '0010_add_world_snapshots'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'chapters',
        sa.Column(
            'execution_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        'chapter_drafts',
        sa.Column(
            'execution_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column('chapters', 'execution_context', server_default=None)
    op.alter_column('chapter_drafts', 'execution_context', server_default=None)


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'execution_context')
    op.drop_column('chapters', 'execution_context')
