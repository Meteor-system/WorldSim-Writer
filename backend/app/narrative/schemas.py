from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.schemas import BeatCard


class ExecutionContextPov(BaseModel):
    model_config = ConfigDict(extra='forbid')

    character_id: int | None = None
    name: str | None = None


class ExecutionContextPriorityCharacter(BaseModel):
    model_config = ConfigDict(extra='forbid')

    character_id: int
    name: str
    role_type: str
    status: str
    reason: str


class ExecutionContextPriorityForeshadow(BaseModel):
    model_config = ConfigDict(extra='forbid')

    foreshadow_id: int
    title: str
    status: str
    urgency_level: int
    reason: str


class ExecutionContextProgressionHint(BaseModel):
    model_config = ConfigDict(extra='forbid')

    hint_type: str
    priority: str
    title: str
    rationale: str
    suggested_next_beat: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)
    can_seed_next_chapter_goal: bool = False


class ExecutionContextContinuityWarning(BaseModel):
    model_config = ConfigDict(extra='forbid')

    severity: str
    category: str
    message: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)


class ExecutionContextRecentEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')

    id: int
    event_type: str
    world_version_before: int
    world_version_after: int
    created_at: str


class ExecutionContextMaterialReference(BaseModel):
    model_config = ConfigDict(extra='forbid')

    asset_id: int
    batch_id: int
    asset_pool: str
    title: str
    summary: str
    source_title: str
    source_type: str
    created_at: str
    safety_note: str


class ExecutionContextStyleHandbookDimension(BaseModel):
    model_config = ConfigDict(extra='forbid')

    label: str
    value: str
    evidence: str | None = None


class ExecutionContextStyleHandbookDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')

    narrative_pacing: ExecutionContextStyleHandbookDimension
    language_density: ExecutionContextStyleHandbookDimension
    dialogue_ratio: ExecutionContextStyleHandbookDimension
    scene_progression: ExecutionContextStyleHandbookDimension
    suspense_structure: ExecutionContextStyleHandbookDimension
    relationship_tension: ExecutionContextStyleHandbookDimension
    foreshadowing_pattern: ExecutionContextStyleHandbookDimension
    do_guidelines: list[str] = Field(default_factory=list)
    avoid_guidelines: list[str] = Field(default_factory=list)
    originality_guidelines: list[str] = Field(default_factory=list)


class ExecutionContextStyleHandbookReference(BaseModel):
    model_config = ConfigDict(extra='forbid')

    source_title: str
    source_rights: Literal['own_work', 'authorized', 'public_domain', 'general_reference']
    handbook: ExecutionContextStyleHandbookDraft
    safety_notes: list[str] = Field(default_factory=list)


class ChapterExecutionContext(BaseModel):
    model_config = ConfigDict(extra='forbid')

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
    material_references: list[ExecutionContextMaterialReference] = Field(default_factory=list)
    style_handbook_reference: ExecutionContextStyleHandbookReference | None = None


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


class ApproveRequest(BaseModel):
    draft_version: int | None = None
    selected_character_change_indexes: list[int] | None = None
    selected_foreshadow_change_indexes: list[int] | None = None


class ConsistencyWarning(BaseModel):
    severity: Literal['info', 'warning', 'blocking']
    category: str
    message: str
    object_type: Literal['character', 'foreshadow', 'chapter']
    object_id: int | None = None
    change_index: int | None = None
    details: dict = Field(default_factory=dict)


class ConsistencySummary(BaseModel):
    status: Literal['clear', 'needs_review', 'blocked']
    total: int
    info_count: int
    warning_count: int
    blocking_count: int


class ApprovalConsistencyResponse(BaseModel):
    chapter_id: int
    draft_version: int
    selected_change_indexes: dict
    consistency_summary: ConsistencySummary
    consistency_warnings: list[ConsistencyWarning]


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


class ReviseDraftRequest(BaseModel):
    instruction: str = Field(min_length=3)


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


class ApprovalReadinessWorldVersion(BaseModel):
    source_world_version: int
    current_world_version: int
    matches: bool


class ApprovalReadinessCheck(BaseModel):
    key: str
    label: str
    status: Literal['pass', 'warning', 'fail']
    message: str
    details: dict | list | None = None


class ApprovalReadinessResponse(BaseModel):
    chapter_id: int
    draft_version: int
    ready: bool
    status: Literal['ready', 'needs_review', 'blocked']
    summary: str
    world_version: ApprovalReadinessWorldVersion
    checks: list[ApprovalReadinessCheck]
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    high_risk_items: list[dict] = Field(default_factory=list)


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
