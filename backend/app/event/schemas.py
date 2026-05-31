from datetime import datetime

from pydantic import BaseModel


class EventLogResponse(BaseModel):
    id: int
    world_id: int
    chapter_id: int | None
    event_type: str
    source_type: str
    commit_id: str
    payload: dict
    world_version_before: int
    world_version_after: int
    created_at: datetime

    model_config = {'from_attributes': True}


class EventLogSummaryResponse(BaseModel):
    total: int
    event_type_counts: dict[str, int]
    latest_world_version: int


class EventLogListResponse(BaseModel):
    items: list[EventLogResponse]
    total: int
    limit: int
    offset: int
    summary: EventLogSummaryResponse
