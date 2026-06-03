from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceType = Literal['pasted_text', 'markdown', 'txt']
AssetPool = Literal['inspiration', 'character', 'canon']
ImportStatus = Literal['confirmed']
CandidateStatus = Literal['candidate']


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class ImportConflict(BaseModel):
    severity: Literal['info', 'warning', 'blocking'] = 'warning'
    category: str
    message: str
    matched_text: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ImportCandidateAssetPreview(BaseModel):
    asset_pool: AssetPool
    title: str
    summary: str
    raw_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('title', 'summary', 'raw_text')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class ImportPreviewRequest(BaseModel):
    source_type: SourceType
    source_title: str
    content: str = Field(min_length=1, max_length=50000)

    @field_validator('source_title', 'content')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class ImportPreviewResponse(BaseModel):
    world_id: int
    source_type: SourceType
    source_title: str
    cleaned_excerpt: str
    assets: list[ImportCandidateAssetPreview]
    conflicts: list[ImportConflict]
    asset_counts: dict[str, int]


class ImportConfirmRequest(ImportPreviewRequest):
    assets: list[ImportCandidateAssetPreview]
    conflicts: list[ImportConflict] = Field(default_factory=list)


class ImportCandidateAssetResponse(BaseModel):
    id: int
    world_id: int
    batch_id: int
    asset_pool: AssetPool
    title: str
    summary: str
    raw_text: str
    metadata: dict[str, Any]
    status: CandidateStatus
    created_at: datetime


class ImportBatchResponse(BaseModel):
    id: int
    world_id: int
    source_type: SourceType
    source_title: str
    original_excerpt: str
    cleaned_excerpt: str
    status: ImportStatus
    asset_counts: dict[str, int]
    conflicts: list[ImportConflict]
    created_at: datetime
    confirmed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ImportConfirmResponse(BaseModel):
    batch: ImportBatchResponse
    assets: list[ImportCandidateAssetResponse]


class ImportBatchWithAssetsResponse(ImportBatchResponse):
    assets: list[ImportCandidateAssetResponse]


class ImportBatchListResponse(BaseModel):
    world_id: int
    batches: list[ImportBatchWithAssetsResponse]
