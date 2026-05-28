from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.narrative.models import Chapter
from app.narrative.schemas import ChapterResponse, DraftRequest, DraftResponse
from app.narrative.service import approve_chapter, create_chapter_draft
from app.world.service import require_owned_world

router = APIRouter(tags=['narrative'])


@router.post('/worlds/{world_id}/chapters/draft', response_model=DraftResponse)
def draft_chapter(
    world_id: int,
    payload: DraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(create_chapter_draft(db, current_user, world_id, payload.chapter_goal))


@router.post('/chapters/{chapter_id}/approve', response_model=ChapterResponse)
def approve(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    return ChapterResponse.model_validate(approve_chapter(db, current_user, chapter_id))


@router.post('/chapters/{chapter_id}/reject', response_model=ChapterResponse)
def reject(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    require_owned_world(db, current_user, chapter.world_id)
    chapter.status = 'rejected'
    db.commit()
    db.refresh(chapter)
    return ChapterResponse.model_validate(chapter)
