from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.foreshadow.models import Foreshadow
from app.foreshadow.schemas import ForeshadowCreate, ForeshadowUpdate
from app.narrative.models import Chapter
from app.world.service import require_owned_world


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
    require_owned_world(db, user, world_id)
    _validate_source_chapter(db, world_id, data.source_chapter_id)
    related_character_ids = _validate_related_characters(db, world_id, data.related_character_ids)
    foreshadow = Foreshadow(
        world_id=world_id,
        source_chapter_id=data.source_chapter_id,
        title=data.title,
        description=data.description,
        foreshadow_type=data.foreshadow_type,
        status=data.status if data.status is not None else 'planted',
        urgency_level=data.urgency_level if data.urgency_level is not None else 1,
        related_character_ids=related_character_ids,
        expected_resolution_window=data.expected_resolution_window,
    )
    db.add(foreshadow)
    db.commit()
    db.refresh(foreshadow)
    return foreshadow


def get_foreshadows(db: Session, user: User, world_id: int) -> list[Foreshadow]:
    require_owned_world(db, user, world_id)
    return list(
        db.scalars(
            select(Foreshadow).where(Foreshadow.world_id == world_id).order_by(Foreshadow.id)
        )
    )


def _require_owned_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    foreshadow = db.get(Foreshadow, foreshadow_id)
    if foreshadow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if foreshadow.world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return foreshadow


def get_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    return _require_owned_foreshadow(db, user, foreshadow_id)


def update_foreshadow(db: Session, user: User, foreshadow_id: int, data: ForeshadowUpdate) -> Foreshadow:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    update_data = data.model_dump(exclude_unset=True)
    if 'source_chapter_id' in update_data:
        _validate_source_chapter(db, foreshadow.world_id, update_data['source_chapter_id'])
    if 'related_character_ids' in update_data:
        update_data['related_character_ids'] = _validate_related_characters(
            db,
            foreshadow.world_id,
            update_data['related_character_ids'],
        )
    for field, value in update_data.items():
        setattr(foreshadow, field, value)
    db.commit()
    db.refresh(foreshadow)
    return foreshadow


def delete_foreshadow(db: Session, user: User, foreshadow_id: int) -> None:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    db.delete(foreshadow)
    db.commit()
