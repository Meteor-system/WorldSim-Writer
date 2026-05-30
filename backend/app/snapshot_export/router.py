from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.snapshot_export.schemas import (
    WorldMarkdownExportResponse,
    WorldSnapshotCreate,
    WorldSnapshotDetailResponse,
    WorldSnapshotListResponse,
    WorldSnapshotSummary,
)
from app.snapshot_export.service import create_world_snapshot, export_world_markdown, get_world_snapshot_detail, list_world_snapshots

router = APIRouter(tags=['snapshot-export'])


@router.post('/worlds/{world_id}/snapshots', response_model=WorldSnapshotSummary)
def create_snapshot(
    world_id: int,
    payload: WorldSnapshotCreate | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldSnapshotSummary:
    data = payload or WorldSnapshotCreate()
    return WorldSnapshotSummary.model_validate(create_world_snapshot(db, current_user, world_id, data))


@router.get('/worlds/{world_id}/snapshots', response_model=WorldSnapshotListResponse)
def list_snapshots(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldSnapshotListResponse:
    return WorldSnapshotListResponse.model_validate(list_world_snapshots(db, current_user, world_id))


@router.get('/snapshots/{snapshot_id}', response_model=WorldSnapshotDetailResponse)
def get_snapshot(
    snapshot_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldSnapshotDetailResponse:
    return WorldSnapshotDetailResponse.model_validate(get_world_snapshot_detail(db, current_user, snapshot_id))


@router.post('/worlds/{world_id}/export/markdown', response_model=WorldMarkdownExportResponse)
def export_markdown(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldMarkdownExportResponse:
    return WorldMarkdownExportResponse.model_validate(export_world_markdown(db, current_user, world_id))
