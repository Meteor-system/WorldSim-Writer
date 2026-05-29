from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.character.schemas import CharacterRelationCreate, CharacterRelationUpdate
from app.world.governance import commit_manual_world_change, require_owned_world_for_update
from app.world.service import relation_projection, require_owned_world


def _validate_relation_characters(db: Session, world_id: int, source_character_id: int, target_character_id: int) -> None:
    if source_character_id == target_character_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_SELF_RELATION')
    character_ids = {source_character_id, target_character_id}
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


def create_relation(db: Session, user: User, world_id: int, data: CharacterRelationCreate) -> CharacterRelation:
    world = require_owned_world_for_update(db, user, world_id)
    _validate_relation_characters(db, world.id, data.source_character_id, data.target_character_id)
    relation = CharacterRelation(
        world_id=world.id,
        source_character_id=data.source_character_id,
        target_character_id=data.target_character_id,
        relation_type=data.relation_type,
        intensity=data.intensity,
        visibility=data.visibility,
    )
    db.add(relation)
    db.flush()
    after = relation_projection(relation)
    commit_manual_world_change(
        db,
        world,
        object_type='relation',
        object_id=relation.id,
        action='created',
        before=None,
        after=after,
        edit_reason=data.edit_reason,
    )
    db.refresh(relation)
    return relation


def get_relations(db: Session, user: User, world_id: int) -> list[CharacterRelation]:
    require_owned_world(db, user, world_id)
    return list(
        db.scalars(
            select(CharacterRelation).where(CharacterRelation.world_id == world_id).order_by(CharacterRelation.id)
        )
    )


def _require_owned_relation(db: Session, user: User, relation_id: int) -> CharacterRelation:
    relation = db.get(CharacterRelation, relation_id)
    if relation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if relation.world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return relation


def get_relation(db: Session, user: User, relation_id: int) -> CharacterRelation:
    return _require_owned_relation(db, user, relation_id)


def update_relation(db: Session, user: User, relation_id: int, data: CharacterRelationUpdate) -> CharacterRelation:
    relation = _require_owned_relation(db, user, relation_id)
    world = require_owned_world_for_update(db, user, relation.world_id)
    before = relation_projection(relation)
    update_data = data.model_dump(exclude_unset=True)
    edit_reason = update_data.pop('edit_reason', None)
    source_character_id = update_data.get('source_character_id', relation.source_character_id)
    target_character_id = update_data.get('target_character_id', relation.target_character_id)
    _validate_relation_characters(db, relation.world_id, source_character_id, target_character_id)
    for field, value in update_data.items():
        setattr(relation, field, value)
    db.flush()
    after = relation_projection(relation)
    commit_manual_world_change(
        db,
        world,
        object_type='relation',
        object_id=relation.id,
        action='updated',
        before=before,
        after=after,
        edit_reason=edit_reason,
    )
    db.refresh(relation)
    return relation


def delete_relation(db: Session, user: User, relation_id: int, edit_reason: str | None = None) -> None:
    relation = _require_owned_relation(db, user, relation_id)
    world = require_owned_world_for_update(db, user, relation.world_id)
    before = relation_projection(relation)
    db.delete(relation)
    db.flush()
    commit_manual_world_change(
        db,
        world,
        object_type='relation',
        object_id=relation_id,
        action='deleted',
        before=before,
        after=None,
        edit_reason=edit_reason,
    )
