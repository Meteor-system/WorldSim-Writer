import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError


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


class CritiqueIssue(BaseModel):
    category: str
    severity: str
    message: str


class CritiqueReport(BaseModel):
    score: int = Field(ge=0, le=100)
    issues: list[CritiqueIssue]
    suggestions: list[str]
    consistency_check: dict[str, Any]


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


def parse_critique_report(raw_text: str) -> CritiqueReport:
    try:
        payload = _load_json(raw_text)
        return CritiqueReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc
