from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.narrative_control_center.schemas import (
    ApprovedChapterHistoryDetailResponse,
    ApprovedChapterHistoryResponse,
    NextChapterPrepResponse,
)
from app.narrative_control_center.service import (
    get_approved_chapter_history,
    get_approved_chapter_history_detail,
    get_next_chapter_prep,
)

router = APIRouter(tags=['narrative-control-center'])


@router.get('/worlds/{world_id}/chapters/history', response_model=ApprovedChapterHistoryResponse)
def approved_chapter_history(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ApprovedChapterHistoryResponse:
    return ApprovedChapterHistoryResponse.model_validate(get_approved_chapter_history(db, current_user, world_id))


@router.get('/chapters/{chapter_id}/history', response_model=ApprovedChapterHistoryDetailResponse)
def approved_chapter_history_detail(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ApprovedChapterHistoryDetailResponse:
    return ApprovedChapterHistoryDetailResponse.model_validate(
        get_approved_chapter_history_detail(db, current_user, chapter_id)
    )


@router.get('/worlds/{world_id}/next-chapter-prep', response_model=NextChapterPrepResponse)
def next_chapter_prep(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> NextChapterPrepResponse:
    return NextChapterPrepResponse.model_validate(get_next_chapter_prep(db, current_user, world_id))
