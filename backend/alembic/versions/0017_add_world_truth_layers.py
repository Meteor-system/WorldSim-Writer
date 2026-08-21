"""add world truth layers

Revision ID: 0017_add_world_truth_layers
Revises: 0016_add_character_gender
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0017_add_world_truth_layers'
down_revision: str | None = '0016_add_character_gender'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('worlds', sa.Column('truth_layers', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('worlds', 'truth_layers')
