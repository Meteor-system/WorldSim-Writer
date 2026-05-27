from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class Character(Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default='active')
    public_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    hidden_traits: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    destiny_flag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_goals: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    world: Mapped['World'] = relationship('World', back_populates='characters')


class CharacterRelation(Base):
    __tablename__ = 'character_relations'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    source_character_id: Mapped[int] = mapped_column(
        ForeignKey('characters.id', ondelete='CASCADE'), nullable=False
    )
    target_character_id: Mapped[int] = mapped_column(
        ForeignKey('characters.id', ondelete='CASCADE'), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    visibility: Mapped[str] = mapped_column(String(40), nullable=False, default='public')

    world: Mapped['World'] = relationship('World')
