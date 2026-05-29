from typing import Literal

from pydantic import BaseModel, Field

from app.llm.schemas import BeatCard


class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)


class CreateChapterRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    title: str | None = None


class OutlineRequest(BaseModel):
    chapter_context: str | None = None


class WriteRequest(BaseModel):
    outline_beats: list[BeatCard] | None = None


class DraftResponse(BaseModel):
    chapter_id: int
    draft_id: int
    draft_version: int
    title: str
    content: str
    context_summary: str
    review_hints: list[str]
    proposed_changes: dict
    source_world_version: int
    change_type: str
    change_summary: str | None = None
    parent_draft_version: int | None = None
    status: str | None = None
    approved_content: str | None = None
    rejection_feedback: str | None = None
    outline_beats: list[dict] | None = None
    outline_context: dict | None = None
    critique_report: dict | None = None


class RejectRequest(BaseModel):
    feedback: str = Field(min_length=1)


class EditDraftRequest(BaseModel):
    content: str = Field(min_length=10)
    change_summary: str | None = None


class StashDraftRequest(BaseModel):
    note: str | None = None


class ParagraphDraftRequest(BaseModel):
    paragraph_index: int = Field(ge=0)
    mode: Literal['rewrite', 'polish']
    instruction: str | None = None


class ChapterPipelineResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    draft_version: int
    approved_version: int | None
    base_world_version: int
    approved_content: str | None
    chapter_goal: str | None
    outline_beats: list[dict]
    outline_context: dict
    critique_report: dict

    model_config = {'from_attributes': True}


class OutlineResponse(BaseModel):
    chapter_id: int
    outline_beats: list[dict]
    outline_context: dict
    status: str


class CritiqueResponse(BaseModel):
    chapter_id: int
    critique_report: dict
    status: str


class CriticReportResponse(BaseModel):
    chapter_id: int
    draft_version: int
    current_draft_version: int
    is_stale: bool
    overall_score: int
    summary: str
    dimensions: dict
    issues: list[dict]
    suggestions: list[str]
    created_at: str


class ChapterResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    draft_version: int
    approved_version: int | None
    base_world_version: int
    approved_content: str | None
    chapter_goal: str | None = None
    outline_beats: list[dict] | None = None
    outline_context: dict | None = None
    critique_report: dict | None = None

    model_config = {'from_attributes': True}
