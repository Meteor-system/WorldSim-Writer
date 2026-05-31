from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class TagCreateRequest(BaseModel):
    name: str
    color: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator('color')
    @classmethod
    def normalize_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TagUpdateRequest(BaseModel):
    name: str | None = None
    color: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)

    @field_validator('color')
    @classmethod
    def normalize_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TagMergeRequest(BaseModel):
    target_tag_id: int

    @field_validator('target_tag_id')
    @classmethod
    def validate_target_tag_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError('target_tag_id must be positive')
        return value


class TagMergeResponse(BaseModel):
    world_id: int
    source_tag_id: int
    target_tag_id: int
    moved_count: int
    already_assigned_count: int
    deleted_source_tag: bool


class ObjectTagAssignRequest(BaseModel):
    object_type: str
    object_id: int

    @field_validator('object_type')
    @classmethod
    def validate_object_type(cls, value: str) -> str:
        return _strip_required(value)


class ObjectTagBulkAssignRequest(BaseModel):
    object_type: str
    object_ids: list[int]

    @field_validator('object_type')
    @classmethod
    def validate_object_type(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator('object_ids')
    @classmethod
    def validate_object_ids(cls, value: list[int]) -> list[int]:
        if not value or len(value) > 100 or any(object_id <= 0 for object_id in value):
            raise ValueError('object_ids must contain 1 to 100 positive ids')
        return value


class ObjectTagBulkAssignResponse(BaseModel):
    world_id: int
    tag_id: int
    object_type: str
    requested_count: int
    assigned_count: int
    already_assigned_count: int
    assigned_object_ids: list[int]
    already_assigned_object_ids: list[int]


class TagResponse(BaseModel):
    id: int
    world_id: int
    name: str
    slug: str
    color: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagSummaryResponse(TagResponse):
    assignment_count: int
    object_type_counts: dict[str, int]


class TaggedObjectSummary(BaseModel):
    object_type: str
    object_id: int
    title: str
    subtitle: str
    snippet: str
    metadata: dict[str, Any]


class ObjectTagResponse(BaseModel):
    id: int
    world_id: int
    tag_id: int
    object_type: str
    object_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    world_id: int
    tags: list[TagSummaryResponse]


class TagDetailResponse(BaseModel):
    tag: TagSummaryResponse
    objects: list[TaggedObjectSummary]
