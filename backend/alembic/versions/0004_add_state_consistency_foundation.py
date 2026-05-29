"""add state consistency foundation

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'worlds',
        sa.Column(
            'current_characters',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        'worlds',
        sa.Column(
            'current_foreshadows',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column('event_logs', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_event_logs_chapter_id_chapters',
        'event_logs',
        'chapters',
        ['chapter_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(op.f('ix_event_logs_chapter_id'), 'event_logs', ['chapter_id'], unique=False)
    op.create_index('ix_event_logs_world_created_at', 'event_logs', ['world_id', 'created_at'], unique=False)
    op.create_index('ix_event_logs_world_event_type_created_at', 'event_logs', ['world_id', 'event_type', 'created_at'], unique=False)

    op.execute(
        """
        UPDATE worlds
        SET current_characters = COALESCE((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', characters.id,
                    'name', characters.name,
                    'role_type', characters.role_type,
                    'status', characters.status,
                    'public_profile', characters.public_profile,
                    'hidden_traits', characters.hidden_traits,
                    'destiny_flag', characters.destiny_flag,
                    'current_goals', characters.current_goals
                ) ORDER BY characters.id
            )
            FROM characters
            WHERE characters.world_id = worlds.id
        ), '[]'::jsonb)
        """
    )
    op.execute(
        """
        UPDATE worlds
        SET current_foreshadows = COALESCE((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', foreshadows.id,
                    'title', foreshadows.title,
                    'description', foreshadows.description,
                    'foreshadow_type', foreshadows.foreshadow_type,
                    'status', foreshadows.status,
                    'urgency_level', foreshadows.urgency_level,
                    'related_character_ids', foreshadows.related_character_ids,
                    'expected_resolution_window', foreshadows.expected_resolution_window
                ) ORDER BY foreshadows.id
            )
            FROM foreshadows
            WHERE foreshadows.world_id = worlds.id
        ), '[]'::jsonb)
        """
    )


def downgrade() -> None:
    op.drop_index('ix_event_logs_world_event_type_created_at', table_name='event_logs')
    op.drop_index('ix_event_logs_world_created_at', table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_chapter_id'), table_name='event_logs')
    op.drop_constraint('fk_event_logs_chapter_id_chapters', 'event_logs', type_='foreignkey')
    op.drop_column('event_logs', 'chapter_id')
    op.drop_column('worlds', 'current_foreshadows')
    op.drop_column('worlds', 'current_characters')
