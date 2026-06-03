from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.import_node.schemas import ImportBatchListResponse, ImportConfirmRequest, ImportConfirmResponse, ImportPreviewRequest, ImportPreviewResponse
from app.import_node.service import confirm_import, list_import_batches, preview_import

router = APIRouter(prefix='/worlds/{world_id}/imports', tags=['imports'])


@router.post('/preview', response_model=ImportPreviewResponse)
def preview(
    world_id: int,
    data: ImportPreviewRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ImportPreviewResponse:
    return preview_import(db, current_user, world_id, data)


@router.post('/confirm', response_model=ImportConfirmResponse)
def confirm(
    world_id: int,
    data: ImportConfirmRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ImportConfirmResponse:
    return confirm_import(db, current_user, world_id, data)


@router.get('', response_model=ImportBatchListResponse)
def list_batches(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ImportBatchListResponse:
    return list_import_batches(db, current_user, world_id)
