from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class ForeshadowCreate(BaseModel):
    source_chapter_id: int | None = None
    title: str
    description: str
    foreshadow_type: str
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class ForeshadowUpdate(BaseModel):
    source_chapter_id: int | None = None
    title: str | None = None
    description: str | None = None
    foreshadow_type: str | None = None
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None

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
