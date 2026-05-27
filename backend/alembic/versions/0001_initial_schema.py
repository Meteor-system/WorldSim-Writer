"""Initial MVP schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'worlds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('genre_template', sa.String(length=80), nullable=False),
        sa.Column('truth_canon', sa.Text(), nullable=False),
        sa.Column('truth_canon_version', sa.Integer(), nullable=False),
        sa.Column('world_version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('tone_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_worlds_owner_id'), 'worlds', ['owner_id'], unique=False)

    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('role_type', sa.String(length=60), nullable=False),
        sa.Column('status', sa.String(length=60), nullable=False),
        sa.Column('public_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hidden_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('destiny_flag', sa.String(length=120), nullable=True),
        sa.Column('current_goals', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_characters_world_id'), 'characters', ['world_id'], unique=False)

    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('pov_character_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('draft_version', sa.Integer(), nullable=False),
        sa.Column('approved_version', sa.Integer(), nullable=True),
        sa.Column('base_world_version', sa.Integer(), nullable=False),
        sa.Column('approved_content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['pov_character_id'], ['characters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chapters_world_id'), 'chapters', ['world_id'], unique=False)

    op.create_table(
        'character_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('source_character_id', sa.Integer(), nullable=False),
        sa.Column('target_character_id', sa.Integer(), nullable=False),
        sa.Column('relation_type', sa.String(length=80), nullable=False),
        sa.Column('intensity', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['source_character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_character_relations_world_id'), 'character_relations', ['world_id'], unique=False)

    op.create_table(
        'foreshadows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('source_chapter_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('foreshadow_type', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('urgency_level', sa.Integer(), nullable=False),
        sa.Column('related_character_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expected_resolution_window', sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(['source_chapter_id'], ['chapters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_foreshadows_world_id'), 'foreshadows', ['world_id'], unique=False)

    op.create_table(
        'chapter_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('draft_version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('context_summary', sa.Text(), nullable=False),
        sa.Column('review_hints', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('proposed_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_world_version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),
    )
    op.create_index(op.f('ix_chapter_drafts_chapter_id'), 'chapter_drafts', ['chapter_id'], unique=False)

    op.create_table(
        'event_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('source_type', sa.String(length=80), nullable=False),
        sa.Column('commit_id', sa.String(length=120), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('world_version_before', sa.Integer(), nullable=False),
        sa.Column('world_version_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_event_logs_commit_id', 'event_logs', ['commit_id'], unique=True)
    op.create_index(op.f('ix_event_logs_world_id'), 'event_logs', ['world_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_event_logs_world_id'), table_name='event_logs')
    op.drop_index('ix_event_logs_commit_id', table_name='event_logs')
    op.drop_table('event_logs')

    op.drop_index(op.f('ix_chapter_drafts_chapter_id'), table_name='chapter_drafts')
    op.drop_table('chapter_drafts')

    op.drop_index(op.f('ix_foreshadows_world_id'), table_name='foreshadows')
    op.drop_table('foreshadows')

    op.drop_index(op.f('ix_character_relations_world_id'), table_name='character_relations')
    op.drop_table('character_relations')

    op.drop_index(op.f('ix_chapters_world_id'), table_name='chapters')
    op.drop_table('chapters')

    op.drop_index(op.f('ix_characters_world_id'), table_name='characters')
    op.drop_table('characters')

    op.drop_index(op.f('ix_worlds_owner_id'), table_name='worlds')
    op.drop_table('worlds')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
