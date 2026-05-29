from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class CharacterCreate(BaseModel):
    name: str
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
    name: str | None = None
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
    role_type: str
    status: str
    public_profile: dict[str, Any]
    hidden_traits: dict[str, Any]
    destiny_flag: str | None
    current_goals: list[str]

    model_config = ConfigDict(from_attributes=True)


class CharacterRelationResponse(BaseModel):
    id: int
    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int
    visibility: str

    model_config = ConfigDict(from_attributes=True)
