"""add chapter draft quality report

Revision ID: 0014_add_chapter_draft_quality_report
Revises: 0013_add_import_node
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0014_add_chapter_draft_quality_report'
down_revision: str | None = '0013_add_import_node'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'chapter_drafts',
        sa.Column(
            'quality_report',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'quality_report')
