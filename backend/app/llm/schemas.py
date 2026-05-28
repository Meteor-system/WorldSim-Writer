import json

from pydantic import BaseModel, ValidationError


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


def parse_chapter_generation(raw_text: str) -> ChapterGeneration:
    try:
        payload = json.loads(raw_text)
        return ChapterGeneration.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc
