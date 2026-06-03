from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class ImportBatch(Base):
    __tablename__ = 'import_batches'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_title: Mapped[str] = mapped_column(String(200), nullable=False)
    original_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default='confirmed')
    asset_counts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    conflicts: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    world: Mapped['World'] = relationship('World')
    assets: Mapped[list['ImportCandidateAsset']] = relationship('ImportCandidateAsset', back_populates='batch', cascade='all, delete-orphan')


class ImportCandidateAsset(Base):
    __tablename__ = 'import_candidate_assets'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('import_batches.id', ondelete='CASCADE'), nullable=False, index=True)
    asset_pool: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default='candidate')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    batch: Mapped[ImportBatch] = relationship('ImportBatch', back_populates='assets')
