from typing import Literal

from pydantic import BaseModel, Field

from app.llm.schemas import BeatCard


class ExecutionContextPov(BaseModel):
    character_id: int | None = None
    name: str | None = None


class ExecutionContextPriorityCharacter(BaseModel):
    character_id: int
    name: str
    role_type: str
    status: str
    reason: str


class ExecutionContextPriorityForeshadow(BaseModel):
    foreshadow_id: int
    title: str
    status: str
    urgency_level: int
    reason: str


class ExecutionContextProgressionHint(BaseModel):
    hint_type: str
    priority: str
    title: str
    rationale: str
    suggested_next_beat: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)
    can_seed_next_chapter_goal: bool = False


class ExecutionContextContinuityWarning(BaseModel):
    severity: str
    category: str
    message: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)


class ExecutionContextRecentEvent(BaseModel):
    id: int
    event_type: str
    world_version_before: int
    world_version_after: int
    created_at: str


class ChapterExecutionContext(BaseModel):
    source: Literal['next_chapter_prep', 'manual'] = 'manual'
    source_world_version: int
    next_chapter_number: int | None = None
    goal: str = Field(min_length=3)
    recommended_pov: ExecutionContextPov = Field(default_factory=ExecutionContextPov)
    source_signals: list[str] = Field(default_factory=list)
    priority_characters: list[ExecutionContextPriorityCharacter] = Field(default_factory=list)
    priority_foreshadows: list[ExecutionContextPriorityForeshadow] = Field(default_factory=list)
    progression_hints: list[ExecutionContextProgressionHint] = Field(default_factory=list)
    continuity_warnings: list[ExecutionContextContinuityWarning] = Field(default_factory=list)
    recent_events: list[ExecutionContextRecentEvent] = Field(default_factory=list)


class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    execution_context: ChapterExecutionContext | None = None


class CreateChapterRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    title: str | None = None
    execution_context: ChapterExecutionContext | None = None


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
    execution_context: dict | None = None


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
    execution_context: dict | None = None

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


class CharacterArcReportResponse(BaseModel):
    chapter_id: int
    draft_version: int
    current_draft_version: int
    is_stale: bool
    summary: str
    character_arcs: list[dict]
    relationship_notes: list[dict]
    progression_hints: list[dict]
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
    execution_context: dict | None = None

    model_config = {'from_attributes': True}
