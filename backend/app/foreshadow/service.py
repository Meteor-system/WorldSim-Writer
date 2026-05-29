from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.foreshadow.models import Foreshadow, ForeshadowEvent
from app.foreshadow.schemas import ForeshadowCreate, ForeshadowUpdate
from app.narrative.models import Chapter
from app.world.governance import commit_manual_world_change, require_owned_world_for_update
from app.world.service import foreshadow_projection, require_owned_world

FORESHADOW_STATUSES = {'planted', 'advanced', 'resolved', 'expired'}
VALID_STATUS_TRANSITIONS = {
    'planted': {'advanced', 'expired'},
    'advanced': {'resolved', 'expired'},
    'resolved': set(),
    'expired': set(),
}


def validate_foreshadow_status(status_value: str) -> None:
    if status_value not in FORESHADOW_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS')


def validate_foreshadow_transition(current_status: str, next_status: str) -> None:
    validate_foreshadow_status(next_status)
    if current_status == next_status:
        return
    if next_status not in VALID_STATUS_TRANSITIONS.get(current_status, set()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS_TRANSITION')


def add_foreshadow_event(
    db: Session,
    foreshadow: Foreshadow,
    event_type: str,
    chapter_id: int | None = None,
    note: str | None = None,
) -> ForeshadowEvent:
    validate_foreshadow_status(event_type)
    event = ForeshadowEvent(
        foreshadow_id=foreshadow.id,
        chapter_id=chapter_id,
        event_type=event_type,
        note=note,
    )
    db.add(event)
    return event


def apply_foreshadow_status_transition(
    db: Session,
    foreshadow: Foreshadow,
    next_status: str,
    chapter_id: int | None = None,
    note: str | None = None,
) -> bool:
    validate_foreshadow_transition(foreshadow.status, next_status)
    if foreshadow.status == next_status:
        return False
    foreshadow.status = next_status
    add_foreshadow_event(db, foreshadow, next_status, chapter_id=chapter_id, note=note)
    return True


def _validate_source_chapter(db: Session, world_id: int, source_chapter_id: int | None) -> None:
    if source_chapter_id is None:
        return
    chapter = db.get(Chapter, source_chapter_id)
    if chapter is None or chapter.world_id != world_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='SOURCE_CHAPTER_NOT_FOUND')


def _validate_related_characters(db: Session, world_id: int, related_character_ids: list[int] | None) -> list[int]:
    if related_character_ids is None:
        return []
    if not related_character_ids:
        return []
    character_ids = set(related_character_ids)
    found_ids = set(
        db.scalars(
            select(Character.id).where(
                Character.world_id == world_id,
                Character.id.in_(character_ids),
            )
        )
    )
    if found_ids != character_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='RELATED_CHARACTER_NOT_FOUND')
    return related_character_ids


def create_foreshadow(db: Session, user: User, world_id: int, data: ForeshadowCreate) -> Foreshadow:
    world = require_owned_world_for_update(db, user, world_id)
    _validate_source_chapter(db, world_id, data.source_chapter_id)
    related_character_ids = _validate_related_characters(db, world_id, data.related_character_ids)
    foreshadow_status = data.status if data.status is not None else 'planted'
    validate_foreshadow_status(foreshadow_status)
    foreshadow = Foreshadow(
        world_id=world_id,
        source_chapter_id=data.source_chapter_id,
        title=data.title,
        description=data.description,
        foreshadow_type=data.foreshadow_type,
        status=foreshadow_status,
        urgency_level=data.urgency_level if data.urgency_level is not None else 1,
        related_character_ids=related_character_ids,
        expected_resolution_window=data.expected_resolution_window,
    )
    db.add(foreshadow)
    db.flush()
    add_foreshadow_event(db, foreshadow, foreshadow.status, chapter_id=foreshadow.source_chapter_id)
    after = foreshadow_projection(foreshadow)
    commit_manual_world_change(
        db,
        world,
        object_type='foreshadow',
        object_id=foreshadow.id,
        action='created',
        before=None,
        after=after,
        edit_reason=data.edit_reason,
    )
    db.refresh(foreshadow)
    return foreshadow


def get_foreshadows(db: Session, user: User, world_id: int, statuses: list[str] | None = None) -> list[Foreshadow]:
    require_owned_world(db, user, world_id)
    if statuses:
        for status_value in statuses:
            validate_foreshadow_status(status_value)
    query = select(Foreshadow).where(Foreshadow.world_id == world_id)
    if statuses:
        query = query.where(Foreshadow.status.in_(statuses))
    return list(db.scalars(query.order_by(Foreshadow.id)))


def _require_owned_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    foreshadow = db.get(Foreshadow, foreshadow_id)
    if foreshadow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if foreshadow.world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return foreshadow


def get_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    return _require_owned_foreshadow(db, user, foreshadow_id)


def get_foreshadow_timeline(db: Session, user: User, foreshadow_id: int) -> list[dict]:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    rows = db.execute(
        select(ForeshadowEvent, Chapter.title)
        .outerjoin(Chapter, ForeshadowEvent.chapter_id == Chapter.id)
        .where(ForeshadowEvent.foreshadow_id == foreshadow.id)
        .order_by(ForeshadowEvent.created_at, ForeshadowEvent.id)
    ).all()
    return [
        {
            'event_type': event.event_type,
            'chapter_id': event.chapter_id,
            'chapter_title': chapter_title,
            'note': event.note,
            'created_at': event.created_at,
        }
        for event, chapter_title in rows
    ]


def update_foreshadow(db: Session, user: User, foreshadow_id: int, data: ForeshadowUpdate) -> Foreshadow:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    world = require_owned_world_for_update(db, user, foreshadow.world_id)
    before = foreshadow_projection(foreshadow)
    update_data = data.model_dump(exclude_unset=True)
    edit_reason = update_data.pop('edit_reason', None)
    if 'source_chapter_id' in update_data:
        _validate_source_chapter(db, foreshadow.world_id, update_data['source_chapter_id'])
    if 'related_character_ids' in update_data:
        update_data['related_character_ids'] = _validate_related_characters(
            db,
            foreshadow.world_id,
            update_data['related_character_ids'],
        )
    next_status = update_data.pop('status', None)
    for field, value in update_data.items():
        setattr(foreshadow, field, value)
    if next_status is not None:
        apply_foreshadow_status_transition(db, foreshadow, next_status)
    db.flush()
    after = foreshadow_projection(foreshadow)
    commit_manual_world_change(
        db,
        world,
        object_type='foreshadow',
        object_id=foreshadow.id,
        action='updated',
        before=before,
        after=after,
        edit_reason=edit_reason,
    )
    db.refresh(foreshadow)
    return foreshadow


def get_stale_foreshadows(db: Session, user: User, world_id: int) -> list[dict]:
    world = require_owned_world(db, user, world_id)
    planted = list(
        db.scalars(
            select(Foreshadow)
            .where(Foreshadow.world_id == world.id)
            .where(Foreshadow.status == 'planted')
            .where(Foreshadow.source_chapter_id.is_not(None))
            .order_by(Foreshadow.id)
        )
    )
    stale = []
    for foreshadow in planted:
        assert foreshadow.source_chapter_id is not None
        count = db.scalar(
            select(func.count())
            .select_from(Chapter)
            .where(Chapter.world_id == world.id)
            .where(Chapter.status == 'approved')
            .where(Chapter.id > foreshadow.source_chapter_id)
        ) or 0
        if count >= 3:
            stale.append(
                {
                    'foreshadow': foreshadow,
                    'chapters_since_planted': count,
                    'alert_level': 'critical' if count >= 6 else 'warning',
                }
            )
    return stale


def delete_foreshadow(db: Session, user: User, foreshadow_id: int, edit_reason: str | None = None) -> None:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    world = require_owned_world_for_update(db, user, foreshadow.world_id)
    before = foreshadow_projection(foreshadow)
    db.delete(foreshadow)
    db.flush()
    commit_manual_world_change(
        db,
        world,
        object_type='foreshadow',
        object_id=foreshadow_id,
        action='deleted',
        before=before,
        after=None,
        edit_reason=edit_reason,
    )
