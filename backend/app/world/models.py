from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.character.models import Character
    from app.event.models import EventLog
    from app.foreshadow.models import Foreshadow
    from app.narrative.models import Chapter


class World(Base):
    __tablename__ = 'worlds'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    genre_template: Mapped[str] = mapped_column(String(80), nullable=False)
    truth_canon: Mapped[str] = mapped_column(Text, nullable=False)
    truth_canon_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    world_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default='active')
    tone_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_characters: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    current_foreshadows: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    current_relations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    story_arc: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner: Mapped['User'] = relationship('User', back_populates='worlds')
    characters: Mapped[list['Character']] = relationship('Character', back_populates='world', cascade='all, delete-orphan')
    foreshadows: Mapped[list['Foreshadow']] = relationship('Foreshadow', back_populates='world', cascade='all, delete-orphan')
    chapters: Mapped[list['Chapter']] = relationship('Chapter', back_populates='world', cascade='all, delete-orphan')
    events: Mapped[list['EventLog']] = relationship('EventLog', back_populates='world', cascade='all, delete-orphan')
