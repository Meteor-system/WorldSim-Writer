from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class EmptyForeshadowDeleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ForeshadowCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    source_chapter_id: int | None = None
    title: str
    description: str
    foreshadow_type: str
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None
    edit_reason: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class ForeshadowUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    source_chapter_id: int | None = None
    title: str | None = None
    description: str | None = None
    foreshadow_type: str | None = None
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None
    edit_reason: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_optional_required_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)


class ForeshadowResponse(BaseModel):
    id: int
    source_chapter_id: int | None
    title: str
    description: str
    foreshadow_type: str
    status: str
    urgency_level: int
    related_character_ids: list[int]
    expected_resolution_window: str | None

    model_config = ConfigDict(from_attributes=True)


class ForeshadowEventResponse(BaseModel):
    event_type: str
    chapter_id: int | None
    chapter_title: str | None
    note: str | None
    created_at: datetime


class StaleForeshadowResponse(BaseModel):
    foreshadow: ForeshadowResponse
    chapters_since_planted: int
    alert_level: Literal['warning', 'critical']


class RelatedCharacterBrief(BaseModel):
    id: int
    name: str
    role_type: str


class ForeshadowLedgerSummary(BaseModel):
    total: int
    open_count: int
    planted_count: int
    advanced_count: int
    resolved_count: int
    expired_count: int
    high_urgency_count: int
    stale_count: int
    overdue_count: int


class ForeshadowLedgerEntry(BaseModel):
    foreshadow: ForeshadowResponse
    status_group: Literal['planted', 'advanced', 'resolved', 'expired']
    is_open: bool
    is_high_urgency: bool
    is_stale: bool
    is_overdue: bool
    chapters_since_planted: int
    pressure_level: Literal['medium', 'high', 'critical', 'resolved', 'expired']
    pressure_reasons: list[str]
    related_characters: list[RelatedCharacterBrief]
    recent_events: list[ForeshadowEventResponse]


class ForeshadowLedgerResponse(BaseModel):
    world_id: int
    world_version: int
    summary: ForeshadowLedgerSummary
    groups: dict[Literal['planted', 'advanced', 'resolved', 'expired'], list[ForeshadowLedgerEntry]]
    high_pressure: list[ForeshadowLedgerEntry]
