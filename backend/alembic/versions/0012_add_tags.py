"""add tags

Revision ID: 0012_add_tags
Revises: 0011_add_chapter_execution_context
Create Date: 2026-05-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0012_add_tags'
down_revision: str | None = '0011_add_chapter_execution_context'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('slug', sa.String(length=140), nullable=False),
        sa.Column('color', sa.String(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('world_id', 'slug', name='uq_tags_world_slug'),
    )
    op.create_index(op.f('ix_tags_world_id'), 'tags', ['world_id'], unique=False)
    op.create_table(
        'object_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('object_type', sa.String(length=40), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_id', 'object_type', 'object_id', name='uq_object_tags_tag_object'),
    )
    op.create_index(op.f('ix_object_tags_tag_id'), 'object_tags', ['tag_id'], unique=False)
    op.create_index(op.f('ix_object_tags_world_id'), 'object_tags', ['world_id'], unique=False)
    op.create_index('ix_object_tags_world_object', 'object_tags', ['world_id', 'object_type', 'object_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_object_tags_world_object', table_name='object_tags')
    op.drop_index(op.f('ix_object_tags_world_id'), table_name='object_tags')
    op.drop_index(op.f('ix_object_tags_tag_id'), table_name='object_tags')
    op.drop_table('object_tags')
    op.drop_index(op.f('ix_tags_world_id'), table_name='tags')
    op.drop_table('tags')
