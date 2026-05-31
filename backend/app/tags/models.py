from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class Tag(Base):
    __tablename__ = 'tags'
    __table_args__ = (UniqueConstraint('world_id', 'slug', name='uq_tags_world_slug'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    world: Mapped['World'] = relationship('World')
    assignments: Mapped[list['ObjectTag']] = relationship('ObjectTag', back_populates='tag', cascade='all, delete-orphan')


class ObjectTag(Base):
    __tablename__ = 'object_tags'
    __table_args__ = (
        UniqueConstraint('tag_id', 'object_type', 'object_id', name='uq_object_tags_tag_object'),
        Index('ix_object_tags_world_object', 'world_id', 'object_type', 'object_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey('tags.id', ondelete='CASCADE'), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(40), nullable=False)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    tag: Mapped['Tag'] = relationship('Tag', back_populates='assignments')
