from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class Chapter(Base):
    __tablename__ = 'chapters'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    pov_character_id: Mapped[int | None] = mapped_column(
        ForeignKey('characters.id', ondelete='SET NULL'), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default='reviewing')
    draft_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approved_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_world_version: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    chapter_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline_beats: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    outline_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    critique_report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    character_arc_report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    world: Mapped['World'] = relationship('World', back_populates='chapters')
    drafts: Mapped[list['ChapterDraft']] = relationship('ChapterDraft', back_populates='chapter', cascade='all, delete-orphan')


class ChapterDraft(Base):
    __tablename__ = 'chapter_drafts'
    __table_args__ = (UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False, index=True)
    draft_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_summary: Mapped[str] = mapped_column(Text, nullable=False)
    review_hints: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    proposed_changes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_world_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rejection_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(40), nullable=False, default='generated')
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_draft_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    chapter: Mapped['Chapter'] = relationship('Chapter', back_populates='drafts')
