from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.narrative.schemas import (
    ChapterPipelineResponse,
    ChapterResponse,
    CharacterArcReportResponse,
    CreateChapterRequest,
    CriticReportResponse,
    CritiqueResponse,
    DraftRequest,
    DraftResponse,
    EditDraftRequest,
    OutlineRequest,
    OutlineResponse,
    ParagraphDraftRequest,
    RejectRequest,
    StashDraftRequest,
    WriteRequest,
)
from app.narrative.service import (
    approve_chapter,
    create_chapter_draft,
    create_chapter_session,
    critique_chapter,
    edit_chapter_draft,
    generate_character_arc_report,
    generate_chapter_outline,
    generate_critic_report,
    get_approval_preview,
    get_character_arc_report,
    get_critic_report,
    get_draft_diff,
    reject_chapter,
    revise_chapter_paragraph,
    stash_chapter_draft,
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


@router.post('/chapters/{chapter_id}/critic-report', response_model=CriticReportResponse)
def create_critic_report(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CriticReportResponse:
    return CriticReportResponse.model_validate(generate_critic_report(db, current_user, chapter_id))


@router.get('/chapters/{chapter_id}/critic-report', response_model=CriticReportResponse)
def read_critic_report(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CriticReportResponse:
    return CriticReportResponse.model_validate(get_critic_report(db, current_user, chapter_id))


@router.post('/chapters/{chapter_id}/character-arc-report', response_model=CharacterArcReportResponse)
def create_character_arc_report(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterArcReportResponse:
    return CharacterArcReportResponse.model_validate(generate_character_arc_report(db, current_user, chapter_id))


@router.get('/chapters/{chapter_id}/character-arc-report', response_model=CharacterArcReportResponse)
def read_character_arc_report(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterArcReportResponse:
    return CharacterArcReportResponse.model_validate(get_character_arc_report(db, current_user, chapter_id))


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
    return DraftResponse.model_validate(
        edit_chapter_draft(db, current_user, chapter_id, payload.content, payload.change_summary)
    )


@router.get('/chapters/{chapter_id}/drafts/diff')
def draft_diff(
    chapter_id: int,
    from_version: int = Query(alias='from'),
    to_version: int = Query(alias='to'),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    return get_draft_diff(db, current_user, chapter_id, from_version, to_version)


@router.get('/chapters/{chapter_id}/approval-preview')
def approval_preview(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    return get_approval_preview(db, current_user, chapter_id)


@router.post('/chapters/{chapter_id}/draft/stash', response_model=DraftResponse)
def stash_draft(
    chapter_id: int,
    payload: StashDraftRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(stash_chapter_draft(db, current_user, chapter_id, payload.note if payload else None))


@router.post('/chapters/{chapter_id}/draft/paragraph', response_model=DraftResponse)
def revise_paragraph(
    chapter_id: int,
    payload: ParagraphDraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(
        revise_chapter_paragraph(
            db,
            current_user,
            chapter_id,
            payload.paragraph_index,
            payload.mode,
            payload.instruction,
        )
    )
