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


class WorldSnapshotCompareChange(BaseModel):
    object_type: str
    object_id: int | None
    change_type: str
    title: str
    fields_changed: list[str] = Field(default_factory=list)
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None


class WorldSnapshotCompareSummary(BaseModel):
    total_changes: int
    object_type_counts: dict[str, int]


class WorldSnapshotCompareResponse(BaseModel):
    world_id: int
    base_snapshot: WorldSnapshotSummary
    target_snapshot: WorldSnapshotSummary
    summary: WorldSnapshotCompareSummary
    changes: dict[str, list[WorldSnapshotCompareChange]]


class MarkdownExportFile(BaseModel):
    path: str
    content: str


class WorldMarkdownExportResponse(BaseModel):
    world_id: int
    world_version: int
    generated_at: datetime
    archive_filename: str
    archive_base64: str
    files: list[MarkdownExportFile]
