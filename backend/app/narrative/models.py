from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.foreshadow.models import Foreshadow
    from app.world.models import World


class Chapter(Base):
    __tablename__ = 'chapters'
    __table_args__ = (Index('ix_chapters_world_status_updated_at', 'world_id', 'status', 'updated_at'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pov_character_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('characters.id'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='drafting', server_default='drafting', index=True)
    draft_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1')
    approved_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_world_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    world: Mapped['World'] = relationship('World', back_populates='chapters')
    drafts: Mapped[list['ChapterDraft']] = relationship('ChapterDraft', back_populates='chapter', cascade='all, delete-orphan')
    foreshadows: Mapped[list['Foreshadow']] = relationship('Foreshadow', back_populates='source_chapter')


class ChapterDraft(Base):
    __tablename__ = 'chapter_drafts'
    __table_args__ = (
        UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),
        Index('ix_chapter_drafts_chapter_draft_version', 'chapter_id', 'draft_version'),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chapter_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False, index=True)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    draft_version: Mapped[int] = mapped_column(Integer, nullable=False)
    base_world_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_events: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    critic_notes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='candidate', server_default='candidate', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    chapter: Mapped['Chapter'] = relationship('Chapter', back_populates='drafts')
    world: Mapped['World'] = relationship('World')
