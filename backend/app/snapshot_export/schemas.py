from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorldSnapshotCreate(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    note: str | None = None


class WorldSnapshotSummary(BaseModel):
    id: int
    world_id: int
    world_version: int
    label: str | None
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorldSnapshotListResponse(BaseModel):
    world_id: int
    snapshots: list[WorldSnapshotSummary]


class WorldSnapshotDetailResponse(WorldSnapshotSummary):
    payload: dict[str, Any]


class MarkdownExportFile(BaseModel):
    path: str
    content: str


class WorldMarkdownExportResponse(BaseModel):
    world_id: int
    world_version: int
    generated_at: datetime
    files: list[MarkdownExportFile]
