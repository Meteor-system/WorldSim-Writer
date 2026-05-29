"""add draft version metadata

Revision ID: 0008_add_draft_version_metadata
Revises: 0007_add_current_relations_projection
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0008_add_draft_version_metadata'
down_revision: str | None = '0007_add_current_relations_projection'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('chapter_drafts', sa.Column('change_type', sa.String(length=40), nullable=False, server_default='generated'))
    op.add_column('chapter_drafts', sa.Column('change_summary', sa.Text(), nullable=True))
    op.add_column('chapter_drafts', sa.Column('parent_draft_version', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'parent_draft_version')
    op.drop_column('chapter_drafts', 'change_summary')
    op.drop_column('chapter_drafts', 'change_type')
