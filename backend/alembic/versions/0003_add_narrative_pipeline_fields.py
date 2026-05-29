"""add narrative pipeline fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('chapters', sa.Column('chapter_goal', sa.Text(), nullable=True))
    op.add_column(
        'chapters',
        sa.Column(
            'outline_beats',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        'chapters',
        sa.Column(
            'outline_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        'chapters',
        sa.Column(
            'critique_report',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('chapters', 'critique_report')
    op.drop_column('chapters', 'outline_context')
    op.drop_column('chapters', 'outline_beats')
    op.drop_column('chapters', 'chapter_goal')
