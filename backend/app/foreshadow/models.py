from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.narrative.models import Chapter
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
    events: Mapped[list['ForeshadowEvent']] = relationship(
        'ForeshadowEvent', back_populates='foreshadow', cascade='all, delete-orphan'
    )


class ForeshadowEvent(Base):
    __tablename__ = 'foreshadow_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    foreshadow_id: Mapped[int] = mapped_column(ForeignKey('foreshadows.id', ondelete='CASCADE'), nullable=False, index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    foreshadow: Mapped['Foreshadow'] = relationship('Foreshadow', back_populates='events')
    chapter: Mapped['Chapter | None'] = relationship('Chapter')
