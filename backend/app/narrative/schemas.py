from pydantic import BaseModel, Field


class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)


class DraftResponse(BaseModel):
    chapter_id: int
    draft_id: int
    title: str
    content: str
    context_summary: str
    review_hints: list[str]
    proposed_changes: dict
    source_world_version: int


class ChapterResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    draft_version: int
    approved_version: int | None
    base_world_version: int
    approved_content: str | None

    model_config = {'from_attributes': True}
