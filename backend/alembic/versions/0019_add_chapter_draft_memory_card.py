"""add memory_card to chapter_drafts

Revision ID: 0019_add_chapter_draft_memory_card
Revises: 0018_add_chapter_memories
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0019_add_chapter_draft_memory_card'
down_revision: str | None = '0018_add_chapter_memories'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('chapter_drafts', sa.Column('memory_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'memory_card')
