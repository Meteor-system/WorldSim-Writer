import json
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator


class BeatCard(BaseModel):
    beat_id: str
    summary: str
    pov_character: str | None = None
    location: str | None = None
    emotional_arc: str
    key_dialogue_hints: list[str]


class ChapterOutline(BaseModel):
    beats: list[BeatCard]
    core_conflict: str
    pov_suggestion: str | None = None
    pacing: str
    role_skill_targets: list[str]


class StoryArcChapter(BaseModel):
    chapter_number: int = Field(ge=1, le=10)
    title: str
    summary: str
    core_conflict: str
    pov_suggestion: str
    foreshadow_hints: list[str] = Field(default_factory=list)

    @field_validator('title', 'summary', 'core_conflict', 'pov_suggestion')
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        return stripped

    @field_validator('foreshadow_hints')
    @classmethod
    def validate_foreshadow_hints(cls, value: list[str]) -> list[str]:
        hints = [hint.strip() for hint in value if hint.strip()]
        if len(hints) != len(value):
            raise ValueError('foreshadow hints must not be blank')
        return hints


class CritiqueIssue(BaseModel):
    category: str
    severity: str
    message: str


class CritiqueReport(BaseModel):
    score: int = Field(ge=0, le=100)
    issues: list[CritiqueIssue]
    suggestions: list[str]
    consistency_check: dict[str, Any]


class LiteraryCriticIssue(BaseModel):
    severity: str
    dimension: str
    message: str
    paragraph_index: int | None = None
    suggested_action: str | None = None


class LiteraryCriticDimension(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    issues: list[LiteraryCriticIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class LiteraryCriticReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    summary: str
    dimensions: dict[str, LiteraryCriticDimension]
    issues: list[LiteraryCriticIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ProposedCharacterChange(BaseModel):
    character_id: int
    status: str | None = None
    current_goals: list[str] | None = None


class ProposedForeshadowChange(BaseModel):
    foreshadow_id: int
    status: str
    description_note: str | None = None


class ChapterGeneration(BaseModel):
    title: str
    draft_content: str
    context_summary: str
    review_hints: list[str]
    proposed_character_changes: list[ProposedCharacterChange]
    proposed_foreshadow_changes: list[ProposedForeshadowChange]


def _load_json(raw_text: str) -> Any:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc


def parse_chapter_generation(raw_text: str) -> ChapterGeneration:
    try:
        payload = _load_json(raw_text)
        return ChapterGeneration.model_validate(payload)
    except ValidationError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc


def parse_chapter_outline(raw_text: str) -> ChapterOutline:
    try:
        payload = _load_json(raw_text)
        return ChapterOutline.model_validate(payload)
    except ValidationError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc


def _validate_story_arc(chapters: list[StoryArcChapter]) -> list[StoryArcChapter]:
    if len(chapters) != 10:
        raise ValueError('MODEL_RESPONSE_INVALID')
    if [chapter.chapter_number for chapter in chapters] != list(range(1, 11)):
        raise ValueError('MODEL_RESPONSE_INVALID')
    return chapters


def parse_story_arc(raw_text: str) -> list[StoryArcChapter]:
    try:
        payload = _load_json(raw_text)
        if not isinstance(payload, list):
            raise ValueError('MODEL_RESPONSE_INVALID')
        chapters = TypeAdapter(list[StoryArcChapter]).validate_python(payload)
        return _validate_story_arc(chapters)
    except (ValidationError, ValueError) as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc


def parse_critique_report(raw_text: str) -> CritiqueReport:
    try:
        payload = _load_json(raw_text)
        return CritiqueReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc


def parse_literary_critic_report(raw_text: str) -> LiteraryCriticReport:
    try:
        payload = _load_json(raw_text)
        return LiteraryCriticReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc
