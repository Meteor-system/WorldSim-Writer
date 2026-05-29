from pydantic import BaseModel


class ApprovedChapterHistoryItem(BaseModel):
    id: int
    title: str
    status: str
    approved_version: int
    base_world_version: int
    world_version_after: int
    approved_excerpt: str
    event_count: int
    character_change_count: int
    foreshadow_change_count: int


class ApprovedChapterHistoryResponse(BaseModel):
    world_id: int
    chapters: list[ApprovedChapterHistoryItem]


class ChapterHistoryEvent(BaseModel):
    id: int
    event_type: str
    source_type: str
    world_version_before: int
    world_version_after: int
    payload: dict
    created_at: str


class ChapterHistoryChange(BaseModel):
    event_type: str
    object_type: str | None = None
    object_id: int | None = None
    before: dict | None = None
    after: dict | None = None
    payload: dict


class ApprovedChapterHistoryDetailResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    approved_version: int
    base_world_version: int
    approved_content: str
    world_version_before: int
    world_version_after: int
    events: list[ChapterHistoryEvent]
    character_changes: list[ChapterHistoryChange]
    foreshadow_changes: list[ChapterHistoryChange]
    critic_summary: str | None = None
    character_arc_summary: str | None = None


class NextChapterPrepCharacter(BaseModel):
    character_id: int
    name: str
    role_type: str
    status: str
    reason: str


class NextChapterPrepForeshadow(BaseModel):
    foreshadow_id: int
    title: str
    status: str
    urgency_level: int
    reason: str


class NextChapterPrepWarning(BaseModel):
    severity: str
    category: str
    message: str
    related_character_ids: list[int]
    related_foreshadow_ids: list[int]


class NextChapterPrepEvent(BaseModel):
    id: int
    event_type: str
    world_version_before: int
    world_version_after: int
    payload: dict
    created_at: str


class NextChapterPrepResponse(BaseModel):
    world_id: int
    world_version: int
    next_chapter_number: int
    suggested_goal: str
    recommended_pov_character_id: int | None = None
    recommended_pov_character_name: str | None = None
    source_signals: list[str]
    priority_characters: list[NextChapterPrepCharacter]
    priority_foreshadows: list[NextChapterPrepForeshadow]
    progression_hints: list[dict]
    continuity_warnings: list[NextChapterPrepWarning]
    recent_events: list[NextChapterPrepEvent]
