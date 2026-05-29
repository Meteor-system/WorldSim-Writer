"""add rejection_feedback to chapter_drafts

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('chapter_drafts', sa.Column('rejection_feedback', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'rejection_feedback')
