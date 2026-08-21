"""add character gender

Revision ID: 0016_add_character_gender
Revises: 0015_add_llm_usage_audits
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0016_add_character_gender'
down_revision: str | None = '0015_add_llm_usage_audits'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('gender', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'gender')
