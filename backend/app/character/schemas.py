from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class EmptyCharacterDeleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


class CharacterCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    gender: str | None = None
    role_type: str
    status: str | None = None
    public_profile: dict[str, Any] | None = None
    hidden_traits: dict[str, Any] | None = None
    destiny_flag: str | None = None
    current_goals: list[str] | None = None
    edit_reason: str | None = None

    @field_validator('name', 'role_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class CharacterUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str | None = None
    gender: str | None = None
    role_type: str | None = None
    status: str | None = None
    public_profile: dict[str, Any] | None = None
    hidden_traits: dict[str, Any] | None = None
    destiny_flag: str | None = None
    current_goals: list[str] | None = None
    edit_reason: str | None = None

    @field_validator('name', 'role_type')
    @classmethod
    def validate_optional_required_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)


class CharacterResponse(BaseModel):
    id: int
    name: str
    gender: str | None
    role_type: str
    status: str
    public_profile: dict[str, Any]
    hidden_traits: dict[str, Any]
    destiny_flag: str | None
    current_goals: list[str]

    model_config = ConfigDict(from_attributes=True)


class CharacterRelationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int = Field(default=1, ge=1, le=5)
    visibility: str = 'public'
    edit_reason: str | None = None

    @field_validator('relation_type')
    @classmethod
    def validate_relation_type(cls, value: str) -> str:
        return _strip_required(value)


class CharacterRelationUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    source_character_id: int | None = None
    target_character_id: int | None = None
    relation_type: str | None = None
    intensity: int | None = Field(default=None, ge=1, le=5)
    visibility: str | None = None
    edit_reason: str | None = None

    @field_validator('relation_type')
    @classmethod
    def validate_optional_relation_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)


class CharacterRelationResponse(BaseModel):
    id: int
    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int
    visibility: str

    model_config = ConfigDict(from_attributes=True)


class CharacterBatchOperation(BaseModel):
    """Single operation in a batch character update."""
    character_id: int
    action: Literal['tag', 'archive', 'activate', 'set_destiny']
    value: str | None = None


class CharacterBatchUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    operations: list[CharacterBatchOperation] = Field(min_length=1, max_length=50)


class WorldAnomaly(BaseModel):
    """Detected data-governance anomaly."""
    kind: str
    severity: str
    detail: str
    object_type: str | None = None
    object_id: int | None = None
