from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.world.models import World


class Character(Base):
    __tablename__ = 'characters'
    __table_args__ = (Index('ix_characters_world_status', 'world_id', 'status'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    public_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    hidden_traits: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    goals: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    destiny_flag: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='active', server_default='active', index=True)
    faction_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    world: Mapped['World'] = relationship('World', back_populates='characters')
    outgoing_relations: Mapped[list['CharacterRelation']] = relationship(
        'CharacterRelation',
        foreign_keys='CharacterRelation.source_character_id',
        back_populates='source_character',
        cascade='all, delete-orphan',
    )
    incoming_relations: Mapped[list['CharacterRelation']] = relationship(
        'CharacterRelation',
        foreign_keys='CharacterRelation.target_character_id',
        back_populates='target_character',
        cascade='all, delete-orphan',
    )


class CharacterRelation(Base):
    __tablename__ = 'character_relations'
    __table_args__ = (
        Index('ix_character_relations_world_source', 'world_id', 'source_character_id'),
        Index('ix_character_relations_world_target', 'world_id', 'target_character_id'),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('worlds.id'), nullable=False, index=True)
    source_character_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('characters.id'), nullable=False, index=True)
    target_character_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('characters.id'), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='active', server_default='active', index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column('metadata', JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    world: Mapped['World'] = relationship('World')
    source_character: Mapped['Character'] = relationship(
        'Character', foreign_keys=[source_character_id], back_populates='outgoing_relations'
    )
    target_character: Mapped['Character'] = relationship(
        'Character', foreign_keys=[target_character_id], back_populates='incoming_relations'
    )
