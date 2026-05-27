from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.narrative.models import Chapter
    from app.world.models import World


class Foreshadow(Base):
    __tablename__ = 'foreshadows'
    __table_args__ = (
        Index('ix_foreshadows_world_status_urgency', 'world_id', 'status', 'urgency_level'),
        Index('ix_foreshadows_world_source_chapter', 'world_id', 'source_chapter_id'),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    source_chapter_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    foreshadow_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='planted', server_default='planted', index=True)
    urgency_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1', index=True)
    related_character_ids: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    world: Mapped['World'] = relationship('World', back_populates='foreshadows')
    source_chapter: Mapped['Chapter | None'] = relationship('Chapter', back_populates='foreshadows')
