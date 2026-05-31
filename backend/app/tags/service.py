import json
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.narrative.models import Chapter
from app.tags.models import ObjectTag, Tag
from app.tags.schemas import ObjectTagAssignRequest, ObjectTagBulkAssignRequest, TagCreateRequest, TagMergeRequest, TagUpdateRequest
from app.world.service import require_owned_world

SUPPORTED_OBJECT_TYPES = {'character', 'foreshadow', 'chapter', 'event'}


def _slugify(name: str) -> str:
    lowered = name.strip().lower().replace('_', '-')
    collapsed = re.sub(r'\s+', '-', lowered)
    cleaned = re.sub(r'[^\w\-一-鿿]+', '', collapsed)
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='TAG_NAME_REQUIRED')
    return cleaned


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _snippet(text: str, size: int = 140) -> str:
    compact = ' '.join(text.split())
    return compact[:size]


def _require_tag(db: Session, world_id: int, tag_id: int) -> Tag:
    tag = db.get(Tag, tag_id)
    if tag is None or tag.world_id != world_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='TAG_NOT_FOUND')
    return tag


def _validate_object_type(object_type: str) -> str:
    normalized = object_type.strip().lower()
    if normalized not in SUPPORTED_OBJECT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='UNSUPPORTED_TAG_OBJECT_TYPE')
    return normalized


def _target_object(db: Session, world_id: int, object_type: str, object_id: int):
    model = {
        'character': Character,
        'foreshadow': Foreshadow,
        'chapter': Chapter,
        'event': EventLog,
    }[object_type]
    target = db.get(model, object_id)
    if target is None or target.world_id != world_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='TAG_OBJECT_NOT_FOUND')
    return target


def _tag_summary(db: Session, tag: Tag) -> dict:
    rows = db.execute(
        select(ObjectTag.object_type, func.count())
        .where(ObjectTag.tag_id == tag.id)
        .group_by(ObjectTag.object_type)
        .order_by(ObjectTag.object_type)
    ).all()
    counts = {object_type: count for object_type, count in rows}
    return {
        'id': tag.id,
        'world_id': tag.world_id,
        'name': tag.name,
        'slug': tag.slug,
        'color': tag.color,
        'created_at': tag.created_at,
        'assignment_count': sum(counts.values()),
        'object_type_counts': counts,
    }


def _object_summary(target, object_type: str) -> dict[str, Any]:
    if object_type == 'character':
        goals = _json_text(target.current_goals)
        return {
            'object_type': object_type,
            'object_id': target.id,
            'title': target.name,
            'subtitle': f'Character · {target.role_type} · {target.status}',
            'snippet': _snippet(goals),
            'metadata': {'status': target.status, 'role_type': target.role_type},
        }
    if object_type == 'foreshadow':
        return {
            'object_type': object_type,
            'object_id': target.id,
            'title': target.title,
            'subtitle': f'Foreshadow · {target.status} · urgency {target.urgency_level}',
            'snippet': _snippet(target.description),
            'metadata': {'status': target.status, 'urgency_level': target.urgency_level},
        }
    if object_type == 'chapter':
        text = target.chapter_goal or target.approved_content or ''
        return {
            'object_type': object_type,
            'object_id': target.id,
            'title': target.title,
            'subtitle': f'Chapter · {target.status} · world v{target.base_world_version}',
            'snippet': _snippet(text),
            'metadata': {'status': target.status, 'approved_version': target.approved_version},
        }
    return {
        'object_type': object_type,
        'object_id': target.id,
        'title': target.event_type,
        'subtitle': f'Event · {target.source_type} · world {target.world_version_before} → {target.world_version_after}',
        'snippet': _snippet(_json_text(target.payload)),
        'metadata': {'world_version_after': target.world_version_after, 'chapter_id': target.chapter_id},
    }


def list_tags(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    tags = list(db.scalars(select(Tag).where(Tag.world_id == world.id).order_by(Tag.name, Tag.id)))
    return {'world_id': world.id, 'tags': [_tag_summary(db, tag) for tag in tags]}


def create_tag(db: Session, user: User, world_id: int, data: TagCreateRequest) -> Tag:
    world = require_owned_world(db, user, world_id)
    name = data.name.strip()
    tag = Tag(world_id=world.id, name=name, slug=_slugify(name), color=data.color)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='TAG_ALREADY_EXISTS') from exc
    db.refresh(tag)
    return tag


def update_tag(db: Session, user: User, world_id: int, tag_id: int, data: TagUpdateRequest) -> Tag:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    if data.name is not None:
        name = data.name.strip()
        tag.name = name
        tag.slug = _slugify(name)
    if 'color' in data.model_fields_set:
        tag.color = data.color
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='TAG_ALREADY_EXISTS') from exc
    db.refresh(tag)
    return tag


def merge_tag(db: Session, user: User, world_id: int, source_tag_id: int, data: TagMergeRequest) -> dict:
    world = require_owned_world(db, user, world_id)
    source_tag = _require_tag(db, world.id, source_tag_id)
    target_tag = _require_tag(db, world.id, data.target_tag_id)
    if source_tag.id == target_tag.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='TAG_MERGE_TARGET_REQUIRED')

    source_assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.tag_id == source_tag.id).order_by(ObjectTag.id)))
    target_assignments = set(
        db.execute(select(ObjectTag.object_type, ObjectTag.object_id).where(ObjectTag.tag_id == target_tag.id)).all()
    )
    moved_count = 0
    already_assigned_count = 0
    for assignment in source_assignments:
        key = (assignment.object_type, assignment.object_id)
        if key in target_assignments:
            db.delete(assignment)
            already_assigned_count += 1
        else:
            assignment.tag_id = target_tag.id
            target_assignments.add(key)
            moved_count += 1

    db.flush()
    db.delete(source_tag)
    db.commit()
    return {
        'world_id': world.id,
        'source_tag_id': source_tag_id,
        'target_tag_id': target_tag.id,
        'moved_count': moved_count,
        'already_assigned_count': already_assigned_count,
        'deleted_source_tag': True,
    }



def delete_tag(db: Session, user: User, world_id: int, tag_id: int) -> None:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    db.delete(tag)
    db.commit()


def assign_tag(db: Session, user: User, world_id: int, tag_id: int, data: ObjectTagAssignRequest) -> ObjectTag:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    object_type = _validate_object_type(data.object_type)
    _target_object(db, world.id, object_type, data.object_id)
    existing = db.scalar(
        select(ObjectTag)
        .where(ObjectTag.tag_id == tag.id)
        .where(ObjectTag.object_type == object_type)
        .where(ObjectTag.object_id == data.object_id)
    )
    if existing is not None:
        return existing
    assignment = ObjectTag(world_id=world.id, tag_id=tag.id, object_type=object_type, object_id=data.object_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def _unique_ids(ids: list[int]) -> list[int]:
    seen = set()
    unique = []
    for object_id in ids:
        if object_id in seen:
            continue
        seen.add(object_id)
        unique.append(object_id)
    return unique


def bulk_assign_tag(db: Session, user: User, world_id: int, tag_id: int, data: ObjectTagBulkAssignRequest) -> dict:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    object_type = _validate_object_type(data.object_type)
    object_ids = _unique_ids(data.object_ids)
    for object_id in object_ids:
        _target_object(db, world.id, object_type, object_id)

    existing_rows = list(
        db.scalars(
            select(ObjectTag)
            .where(ObjectTag.tag_id == tag.id)
            .where(ObjectTag.object_type == object_type)
            .where(ObjectTag.object_id.in_(object_ids))
            .order_by(ObjectTag.object_id)
        )
    )
    existing_ids = {row.object_id for row in existing_rows}
    assigned_ids = [object_id for object_id in object_ids if object_id not in existing_ids]
    for object_id in assigned_ids:
        db.add(ObjectTag(world_id=world.id, tag_id=tag.id, object_type=object_type, object_id=object_id))
    db.commit()
    already_ids = [object_id for object_id in object_ids if object_id in existing_ids]
    return {
        'world_id': world.id,
        'tag_id': tag.id,
        'object_type': object_type,
        'requested_count': len(data.object_ids),
        'assigned_count': len(assigned_ids),
        'already_assigned_count': len(already_ids),
        'assigned_object_ids': assigned_ids,
        'already_assigned_object_ids': already_ids,
    }


def unassign_tag(db: Session, user: User, world_id: int, tag_id: int, object_type: str, object_id: int) -> None:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    normalized_type = _validate_object_type(object_type)
    assignment = db.scalar(
        select(ObjectTag)
        .where(ObjectTag.tag_id == tag.id)
        .where(ObjectTag.object_type == normalized_type)
        .where(ObjectTag.object_id == object_id)
    )
    if assignment is not None:
        db.delete(assignment)
        db.commit()


def get_tag_detail(db: Session, user: User, world_id: int, tag_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.tag_id == tag.id).order_by(ObjectTag.id)))
    objects = []
    for assignment in assignments:
        try:
            target = _target_object(db, world.id, assignment.object_type, assignment.object_id)
        except HTTPException:
            continue
        objects.append(_object_summary(target, assignment.object_type))
    return {'tag': _tag_summary(db, tag), 'objects': objects}
