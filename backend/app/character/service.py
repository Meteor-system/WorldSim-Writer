from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.character.schemas import CharacterCreate, CharacterUpdate
from app.foreshadow.models import Foreshadow
from app.world.governance import commit_manual_world_change, require_owned_world_for_update
from app.world.service import character_projection, require_owned_world


def create_character(db: Session, user: User, world_id: int, data: CharacterCreate) -> Character:
    world = require_owned_world_for_update(db, user, world_id)
    character = Character(
        world_id=world_id,
        name=data.name,
        role_type=data.role_type,
        status=data.status if data.status is not None else 'active',
        public_profile=data.public_profile if data.public_profile is not None else {},
        hidden_traits=data.hidden_traits if data.hidden_traits is not None else {},
        destiny_flag=data.destiny_flag,
        current_goals=data.current_goals if data.current_goals is not None else [],
    )
    db.add(character)
    db.flush()
    after = character_projection(character)
    commit_manual_world_change(
        db,
        world,
        object_type='character',
        object_id=character.id,
        action='created',
        before=None,
        after=after,
        edit_reason=data.edit_reason,
    )
    db.refresh(character)
    return character


def get_characters(db: Session, user: User, world_id: int) -> list[Character]:
    require_owned_world(db, user, world_id)
    return list(
        db.scalars(
            select(Character).where(Character.world_id == world_id).order_by(Character.id)
        )
    )


def _require_owned_character(db: Session, user: User, character_id: int) -> Character:
    character = db.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if character.world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return character


def get_character(db: Session, user: User, character_id: int) -> Character:
    return _require_owned_character(db, user, character_id)


def update_character(db: Session, user: User, character_id: int, data: CharacterUpdate) -> Character:
    character = _require_owned_character(db, user, character_id)
    world = require_owned_world_for_update(db, user, character.world_id)
    before = character_projection(character)
    update_data = data.model_dump(exclude_unset=True)
    edit_reason = update_data.pop('edit_reason', None)
    for field, value in update_data.items():
        setattr(character, field, value)
    db.flush()
    after = character_projection(character)
    commit_manual_world_change(
        db,
        world,
        object_type='character',
        object_id=character.id,
        action='updated',
        before=before,
        after=after,
        edit_reason=edit_reason,
    )
    db.refresh(character)
    return character


def delete_character(db: Session, user: User, character_id: int, edit_reason: str | None = None) -> None:
    character = _require_owned_character(db, user, character_id)
    world = require_owned_world_for_update(db, user, character.world_id)
    before = character_projection(character)
    foreshadows = db.scalars(select(Foreshadow).where(Foreshadow.world_id == character.world_id))
    for foreshadow in foreshadows:
        if character_id in foreshadow.related_character_ids:
            foreshadow.related_character_ids = [
                related_id for related_id in foreshadow.related_character_ids if related_id != character_id
            ]
    db.delete(character)
    db.flush()
    commit_manual_world_change(
        db,
        world,
        object_type='character',
        object_id=character_id,
        action='deleted',
        before=before,
        after=None,
        edit_reason=edit_reason,
    )
