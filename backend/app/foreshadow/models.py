from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class Foreshadow(Base):
    __tablename__ = 'foreshadows'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    source_chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    foreshadow_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default='planted')
    urgency_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    related_character_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    expected_resolution_window: Mapped[str | None] = mapped_column(String(120), nullable=True)

    world: Mapped['World'] = relationship('World', back_populates='foreshadows')
