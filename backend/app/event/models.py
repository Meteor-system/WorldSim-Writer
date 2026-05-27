from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class EventLog(Base):
    __tablename__ = 'event_logs'
    __table_args__ = (
        Index('ix_event_logs_world_created_at', 'world_id', 'created_at'),
        Index('ix_event_logs_world_event_type_created_at', 'world_id', 'event_type', 'created_at'),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    commit_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    world_version_before: Mapped[int] = mapped_column(Integer, nullable=False)
    world_version_after: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    world: Mapped['World'] = relationship('World', back_populates='events')
