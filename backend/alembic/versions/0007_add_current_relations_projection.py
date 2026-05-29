"""add current relations projection

Revision ID: 0007_add_current_relations_projection
Revises: 0006_add_world_story_arc
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0007_add_current_relations_projection'
down_revision: str | None = '0006_add_world_story_arc'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'worlds',
        sa.Column(
            'current_relations',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.execute(
        """
        UPDATE worlds
        SET current_relations = COALESCE((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', character_relations.id,
                    'source_character_id', character_relations.source_character_id,
                    'target_character_id', character_relations.target_character_id,
                    'relation_type', character_relations.relation_type,
                    'intensity', character_relations.intensity,
                    'visibility', character_relations.visibility
                ) ORDER BY character_relations.id
            )
            FROM character_relations
            WHERE character_relations.world_id = worlds.id
        ), '[]'::jsonb)
        """
    )


def downgrade() -> None:
    op.drop_column('worlds', 'current_relations')
