from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.character.schemas import CharacterRelationResponse, CharacterResponse
from app.event.schemas import EventLogListResponse, EventLogResponse
from app.foreshadow.schemas import ForeshadowResponse
from app.llm.schemas import StoryArcChapter


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class StarterCharacterCreate(BaseModel):
    name: str
    role_type: str
    status: str | None = None
    public_profile: dict[str, Any] | None = None
    hidden_traits: dict[str, Any] | None = None
    destiny_flag: str | None = None
    current_goals: list[str] | None = None

    @field_validator('name', 'role_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class StarterRelationCreate(BaseModel):
    source_index: int = Field(ge=0)
    target_index: int = Field(ge=0)
    relation_type: str
    intensity: int = Field(default=1, ge=1, le=5)
    visibility: str = 'public'

    @field_validator('relation_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class StarterForeshadowCreate(BaseModel):
    title: str
    description: str
    foreshadow_type: str
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_indexes: list[int] | None = None
    expected_resolution_window: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class StarterAssetsCreate(BaseModel):
    characters: list[StarterCharacterCreate] = Field(min_length=1)
    relations: list[StarterRelationCreate] = Field(default_factory=list)
    foreshadows: list[StarterForeshadowCreate] = Field(default_factory=list)


class WorldCreateRequest(BaseModel):
    title: str
    genre_template: str
    truth_canon: str
    tone_profile: dict[str, Any] = Field(default_factory=dict)
    starter_assets: StarterAssetsCreate

    @field_validator('title', 'genre_template', 'truth_canon')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class WorldBriefExpandRequest(BaseModel):
    brief: str = Field(min_length=6, max_length=800)

    @field_validator('brief')
    @classmethod
    def validate_brief(cls, value: str) -> str:
        stripped = _strip_required(value)
        if len(stripped) < 6:
            raise ValueError('brief is too short')
        return stripped


class WorldBriefExpansion(BaseModel):
    payload: WorldCreateRequest
    first_chapter_goal: str = ''
    rationale: str = ''
    assumptions: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)

    @field_validator('first_chapter_goal', 'rationale')
    @classmethod
    def validate_optional_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('assumptions', 'safety_notes')
    @classmethod
    def validate_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class WorldBriefExpandResponse(WorldBriefExpansion):
    pass


class WorldStatusUpdateRequest(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {'active', 'archived'}:
            raise ValueError('status must be active or archived')
        return value


class WorldCanonUpdateRequest(BaseModel):
    truth_canon: str
    edit_reason: str | None = None

    @field_validator('truth_canon')
    @classmethod
    def validate_truth_canon(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator('edit_reason')
    @classmethod
    def validate_edit_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class WorldResponse(BaseModel):
    id: int
    title: str
    genre_template: str
    truth_canon: str
    truth_canon_version: int
    world_version: int
    status: str
    tone_profile: dict
    current_characters: list[dict[str, Any]] = Field(default_factory=list)
    current_foreshadows: list[dict[str, Any]] = Field(default_factory=list)
    current_relations: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WorldSeedSummary(BaseModel):
    key: str
    label: str
    genre_template: str
    hook: str
    tension_profile: list[str]
    starter_summary: dict[str, Any]


class WorldSeedDetail(WorldSeedSummary):
    payload: WorldCreateRequest


class WorldSeedListResponse(BaseModel):
    seeds: list[WorldSeedSummary]


class StoryArcResponse(BaseModel):
    world_id: int
    story_arc: list[StoryArcChapter]


class WorldOverviewResponse(WorldResponse):
    characters: list[CharacterResponse]
    relations: list[CharacterRelationResponse]
    foreshadows: list[ForeshadowResponse]
    recent_events: list[EventLogResponse]
    story_arc: list[StoryArcChapter]
    approved_chapter_count: int


class WorldSearchResultResponse(BaseModel):
    object_type: str
    object_id: int | None
    title: str
    subtitle: str
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorldSearchResponse(BaseModel):
    world_id: int
    query: str
    object_type_counts: dict[str, int]
    results: list[WorldSearchResultResponse]
