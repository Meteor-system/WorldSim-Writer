from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.narrative.schemas import (
    ChapterPipelineResponse,
    ChapterResponse,
    CreateChapterRequest,
    CritiqueResponse,
    DraftRequest,
    DraftResponse,
    EditDraftRequest,
    OutlineRequest,
    OutlineResponse,
    RejectRequest,
    WriteRequest,
)
from app.narrative.service import (
    approve_chapter,
    create_chapter_draft,
    create_chapter_session,
    critique_chapter,
    edit_chapter_draft,
    generate_chapter_outline,
    reject_chapter,
    write_chapter_from_outline,
)

router = APIRouter(tags=['narrative'])


@router.post('/worlds/{world_id}/chapters', response_model=ChapterPipelineResponse)
def create_chapter(
    world_id: int,
    payload: CreateChapterRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterPipelineResponse:
    return ChapterPipelineResponse.model_validate(
        create_chapter_session(db, current_user, world_id, payload.chapter_goal, payload.title)
    )


@router.post('/worlds/{world_id}/chapters/draft', response_model=DraftResponse)
def draft_chapter(
    world_id: int,
    payload: DraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(create_chapter_draft(db, current_user, world_id, payload.chapter_goal))


@router.post('/chapters/{chapter_id}/outline', response_model=OutlineResponse)
def outline(
    chapter_id: int,
    payload: OutlineRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> OutlineResponse:
    return OutlineResponse.model_validate(
        generate_chapter_outline(db, current_user, chapter_id, payload.chapter_context if payload else None)
    )


@router.post('/chapters/{chapter_id}/write', response_model=DraftResponse)
def write(
    chapter_id: int,
    payload: WriteRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(
        write_chapter_from_outline(db, current_user, chapter_id, payload.outline_beats if payload else None)
    )


@router.post('/chapters/{chapter_id}/critique', response_model=CritiqueResponse)
def critique(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CritiqueResponse:
    return CritiqueResponse.model_validate(critique_chapter(db, current_user, chapter_id))


@router.post('/chapters/{chapter_id}/approve', response_model=ChapterResponse)
def approve(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    return ChapterResponse.model_validate(approve_chapter(db, current_user, chapter_id))


@router.post('/chapters/{chapter_id}/reject', response_model=DraftResponse)
def reject(
    chapter_id: int,
    payload: RejectRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(reject_chapter(db, current_user, chapter_id, payload.feedback if payload else ''))


@router.put('/chapters/{chapter_id}/draft', response_model=DraftResponse)
def edit_draft(
    chapter_id: int,
    payload: EditDraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(edit_chapter_draft(db, current_user, chapter_id, payload.content))
