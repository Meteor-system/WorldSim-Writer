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
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'worlds',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('genre_template', sa.String(length=100), nullable=True),
        sa.Column('truth_canon', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('truth_canon_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('world_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=False),
        sa.Column('tone_profile', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_worlds_created_at'), 'worlds', ['created_at'], unique=False)
    op.create_index(op.f('ix_worlds_owner_id'), 'worlds', ['owner_id'], unique=False)
    op.create_index(op.f('ix_worlds_status'), 'worlds', ['status'], unique=False)
    op.create_index(op.f('ix_worlds_updated_at'), 'worlds', ['updated_at'], unique=False)
    op.create_index(op.f('ix_worlds_world_version'), 'worlds', ['world_version'], unique=False)

    op.create_table(
        'characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role_type', sa.String(length=100), nullable=True),
        sa.Column('public_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hidden_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('goals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('destiny_flag', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('faction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_characters_created_at'), 'characters', ['created_at'], unique=False)
    op.create_index(op.f('ix_characters_destiny_flag'), 'characters', ['destiny_flag'], unique=False)
    op.create_index(op.f('ix_characters_faction_id'), 'characters', ['faction_id'], unique=False)
    op.create_index(op.f('ix_characters_status'), 'characters', ['status'], unique=False)
    op.create_index(op.f('ix_characters_updated_at'), 'characters', ['updated_at'], unique=False)
    op.create_index(op.f('ix_characters_world_id'), 'characters', ['world_id'], unique=False)
    op.create_index('ix_characters_world_status', 'characters', ['world_id', 'status'], unique=False)

    op.create_table(
        'chapters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=True),
        sa.Column('pov_character_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='drafting', nullable=False),
        sa.Column('draft_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('approved_version', sa.Integer(), nullable=True),
        sa.Column('base_world_version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pov_character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chapters_base_world_version'), 'chapters', ['base_world_version'], unique=False)
    op.create_index(op.f('ix_chapters_created_at'), 'chapters', ['created_at'], unique=False)
    op.create_index(op.f('ix_chapters_pov_character_id'), 'chapters', ['pov_character_id'], unique=False)
    op.create_index(op.f('ix_chapters_status'), 'chapters', ['status'], unique=False)
    op.create_index(op.f('ix_chapters_updated_at'), 'chapters', ['updated_at'], unique=False)
    op.create_index(op.f('ix_chapters_world_id'), 'chapters', ['world_id'], unique=False)
    op.create_index('ix_chapters_world_status_updated_at', 'chapters', ['world_id', 'status', 'updated_at'], unique=False)

    op.create_table(
        'character_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['target_character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_character_relations_created_at'), 'character_relations', ['created_at'], unique=False)
    op.create_index(op.f('ix_character_relations_source_character_id'), 'character_relations', ['source_character_id'], unique=False)
    op.create_index(op.f('ix_character_relations_status'), 'character_relations', ['status'], unique=False)
    op.create_index(op.f('ix_character_relations_target_character_id'), 'character_relations', ['target_character_id'], unique=False)
    op.create_index(op.f('ix_character_relations_updated_at'), 'character_relations', ['updated_at'], unique=False)
    op.create_index(op.f('ix_character_relations_world_id'), 'character_relations', ['world_id'], unique=False)
    op.create_index('ix_character_relations_world_source', 'character_relations', ['world_id', 'source_character_id'], unique=False)
    op.create_index('ix_character_relations_world_target', 'character_relations', ['world_id', 'target_character_id'], unique=False)

    op.create_table(
        'foreshadows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_chapter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('foreshadow_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='planted', nullable=False),
        sa.Column('urgency_level', sa.Integer(), server_default='1', nullable=False),
        sa.Column('related_character_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expected_resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_chapter_id'], ['chapters.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_foreshadows_created_at'), 'foreshadows', ['created_at'], unique=False)
    op.create_index(op.f('ix_foreshadows_source_chapter_id'), 'foreshadows', ['source_chapter_id'], unique=False)
    op.create_index(op.f('ix_foreshadows_status'), 'foreshadows', ['status'], unique=False)
    op.create_index(op.f('ix_foreshadows_updated_at'), 'foreshadows', ['updated_at'], unique=False)
    op.create_index(op.f('ix_foreshadows_urgency_level'), 'foreshadows', ['urgency_level'], unique=False)
    op.create_index(op.f('ix_foreshadows_world_id'), 'foreshadows', ['world_id'], unique=False)
    op.create_index('ix_foreshadows_world_source_chapter', 'foreshadows', ['world_id', 'source_chapter_id'], unique=False)
    op.create_index('ix_foreshadows_world_status_urgency', 'foreshadows', ['world_id', 'status', 'urgency_level'], unique=False)

    op.create_table(
        'chapter_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('draft_version', sa.Integer(), nullable=False),
        sa.Column('base_world_version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('structured_events', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('critic_notes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='candidate', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),
    )
    op.create_index(op.f('ix_chapter_drafts_base_world_version'), 'chapter_drafts', ['base_world_version'], unique=False)
    op.create_index(op.f('ix_chapter_drafts_chapter_id'), 'chapter_drafts', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_chapter_drafts_created_at'), 'chapter_drafts', ['created_at'], unique=False)
    op.create_index(op.f('ix_chapter_drafts_status'), 'chapter_drafts', ['status'], unique=False)
    op.create_index(op.f('ix_chapter_drafts_updated_at'), 'chapter_drafts', ['updated_at'], unique=False)
    op.create_index(op.f('ix_chapter_drafts_world_id'), 'chapter_drafts', ['world_id'], unique=False)
    op.create_index('ix_chapter_drafts_chapter_draft_version', 'chapter_drafts', ['chapter_id', 'draft_version'], unique=False)

    op.create_table(
        'event_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('world_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('commit_id', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('world_version_before', sa.Integer(), nullable=False),
        sa.Column('world_version_after', sa.Integer(), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_event_logs_created_at'), 'event_logs', ['created_at'], unique=False)
    op.create_index('ix_event_logs_commit_id', 'event_logs', ['commit_id'], unique=True)
    op.create_index(op.f('ix_event_logs_event_type'), 'event_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_event_logs_source_id'), 'event_logs', ['source_id'], unique=False)
    op.create_index(op.f('ix_event_logs_world_id'), 'event_logs', ['world_id'], unique=False)
    op.create_index(op.f('ix_event_logs_world_version_after'), 'event_logs', ['world_version_after'], unique=False)
    op.create_index('ix_event_logs_world_created_at', 'event_logs', ['world_id', 'created_at'], unique=False)
    op.create_index('ix_event_logs_world_event_type_created_at', 'event_logs', ['world_id', 'event_type', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_event_logs_world_event_type_created_at', table_name='event_logs')
    op.drop_index('ix_event_logs_world_created_at', table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_world_version_after'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_world_id'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_source_id'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_event_type'), table_name='event_logs')
    op.drop_index('ix_event_logs_commit_id', table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_created_at'), table_name='event_logs')
    op.drop_table('event_logs')

    op.drop_index('ix_chapter_drafts_chapter_draft_version', table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_world_id'), table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_updated_at'), table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_status'), table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_created_at'), table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_chapter_id'), table_name='chapter_drafts')
    op.drop_index(op.f('ix_chapter_drafts_base_world_version'), table_name='chapter_drafts')
    op.drop_table('chapter_drafts')

    op.drop_index('ix_foreshadows_world_status_urgency', table_name='foreshadows')
    op.drop_index('ix_foreshadows_world_source_chapter', table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_world_id'), table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_urgency_level'), table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_updated_at'), table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_status'), table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_source_chapter_id'), table_name='foreshadows')
    op.drop_index(op.f('ix_foreshadows_created_at'), table_name='foreshadows')
    op.drop_table('foreshadows')

    op.drop_index('ix_character_relations_world_target', table_name='character_relations')
    op.drop_index('ix_character_relations_world_source', table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_world_id'), table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_updated_at'), table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_target_character_id'), table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_status'), table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_source_character_id'), table_name='character_relations')
    op.drop_index(op.f('ix_character_relations_created_at'), table_name='character_relations')
    op.drop_table('character_relations')

    op.drop_index('ix_chapters_world_status_updated_at', table_name='chapters')
    op.drop_index(op.f('ix_chapters_world_id'), table_name='chapters')
    op.drop_index(op.f('ix_chapters_updated_at'), table_name='chapters')
    op.drop_index(op.f('ix_chapters_status'), table_name='chapters')
    op.drop_index(op.f('ix_chapters_pov_character_id'), table_name='chapters')
    op.drop_index(op.f('ix_chapters_created_at'), table_name='chapters')
    op.drop_index(op.f('ix_chapters_base_world_version'), table_name='chapters')
    op.drop_table('chapters')

    op.drop_index('ix_characters_world_status', table_name='characters')
    op.drop_index(op.f('ix_characters_world_id'), table_name='characters')
    op.drop_index(op.f('ix_characters_updated_at'), table_name='characters')
    op.drop_index(op.f('ix_characters_status'), table_name='characters')
    op.drop_index(op.f('ix_characters_faction_id'), table_name='characters')
    op.drop_index(op.f('ix_characters_destiny_flag'), table_name='characters')
    op.drop_index(op.f('ix_characters_created_at'), table_name='characters')
    op.drop_table('characters')

    op.drop_index(op.f('ix_worlds_world_version'), table_name='worlds')
    op.drop_index(op.f('ix_worlds_updated_at'), table_name='worlds')
    op.drop_index(op.f('ix_worlds_status'), table_name='worlds')
    op.drop_index(op.f('ix_worlds_owner_id'), table_name='worlds')
    op.drop_index(op.f('ix_worlds_created_at'), table_name='worlds')
    op.drop_table('worlds')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_table('users')
