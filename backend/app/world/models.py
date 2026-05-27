from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
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

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    genre_template: Mapped[str | None] = mapped_column(String(100), nullable=True)
    truth_canon: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    truth_canon_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1')
    world_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1', index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='draft', server_default='draft', index=True)
    tone_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    owner: Mapped['User'] = relationship('User', back_populates='worlds')
    characters: Mapped[list['Character']] = relationship('Character', back_populates='world', cascade='all, delete-orphan')
    foreshadows: Mapped[list['Foreshadow']] = relationship('Foreshadow', back_populates='world', cascade='all, delete-orphan')
    chapters: Mapped[list['Chapter']] = relationship('Chapter', back_populates='world', cascade='all, delete-orphan')
    events: Mapped[list['EventLog']] = relationship('EventLog', back_populates='world', cascade='all, delete-orphan')
