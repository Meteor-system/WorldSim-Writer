from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.event.models import EventLog
from app.world.models import World
from app.world.service import refresh_world_projection


def require_owned_world_for_update(db: Session, user: User, world_id: int) -> World:
    world = db.scalar(select(World).where(World.id == world_id).with_for_update())
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    if world.status == 'archived':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_ARCHIVED')
    return world


def normalize_edit_reason(edit_reason: str | None) -> str | None:
    if edit_reason is None:
        return None
    stripped = edit_reason.strip()
    return stripped or None


def commit_manual_world_change(
    db: Session,
    world: World,
    object_type: str,
    object_id: int,
    action: str,
    before: dict | None,
    after: dict | None,
    edit_reason: str | None = None,
) -> None:
    version_before = world.world_version
    version_after = version_before + 1
    reason = normalize_edit_reason(edit_reason)
    commit_group_id = f'manual-{object_type}-{object_id}-{uuid4().hex}'

    world.world_version = version_after
    db.flush()
    refresh_world_projection(db, world)

    db.add(
        EventLog(
            world_id=world.id,
            chapter_id=None,
            event_type=f'{object_type}_change',
            source_type='manual_edit',
            commit_id=f'{commit_group_id}-{action}',
            payload={
                'commit_group_id': commit_group_id,
                'object_type': object_type,
                'object_id': object_id,
                'action': action,
                'before': before,
                'after': after,
                'edit_reason': reason,
            },
            world_version_before=version_before,
            world_version_after=version_after,
        )
    )
    db.add(
        EventLog(
            world_id=world.id,
            chapter_id=None,
            event_type='world_version_increment',
            source_type='manual_edit',
            commit_id=f'{commit_group_id}-version',
            payload={
                'commit_group_id': commit_group_id,
                'object_type': object_type,
                'object_id': object_id,
                'action': action,
                'world_version_before': version_before,
                'world_version_after': version_after,
                'edit_reason': reason,
            },
            world_version_before=version_before,
            world_version_after=version_after,
        )
    )
    db.commit()


def _normalize_stored_truth_layer(raw: object, index: int) -> dict:
    if not isinstance(raw, dict):
        return {
            'id': f'layer-{index + 1}',
            'title': f'\u7b2c{index + 1}\u5c42',
            'content': '',
            'reveal_at_chapter': 0,
            'frozen': False,
        }
    layer_id = str(raw.get('id') or f'layer-{index + 1}').strip() or f'layer-{index + 1}'
    title = str(raw.get('title') or '').strip() or f'\u7b2c{index + 1}\u5c42'
    try:
        reveal_at = int(raw.get('reveal_at_chapter') or 0)
    except (TypeError, ValueError):
        reveal_at = 0
    return {
        'id': layer_id,
        'title': title,
        'content': str(raw.get('content') or ''),
        'reveal_at_chapter': max(reveal_at, 0),
        'frozen': bool(raw.get('frozen')),
    }


def update_world_truth_layers(
    db: Session,
    user: User,
    world_id: int,
    layers: list[dict],
    edit_reason: str | None = None,
) -> World:
    world = require_owned_world_for_update(db, user, world_id)
    existing = [
        _normalize_stored_truth_layer(raw, index)
        for index, raw in enumerate(world.truth_layers or [])
    ]
    existing_by_id = {layer['id']: layer for layer in existing}
    incoming = [
        {
            'id': str(layer.get('id') or f'layer-{index + 1}').strip() or f'layer-{index + 1}',
            'title': str(layer.get('title') or '').strip() or f'\u7b2c{index + 1}\u5c42',
            'content': str(layer.get('content') or '').strip(),
            'reveal_at_chapter': int(layer.get('reveal_at_chapter') or 0),
            'frozen': bool(layer.get('frozen')),
        }
        for index, layer in enumerate(layers)
    ]
    incoming_ids = {layer['id'] for layer in incoming}

    for layer_id, stored in existing_by_id.items():
        if not stored['frozen']:
            continue
        if layer_id not in incoming_ids:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='FROZEN_TRUTH_LAYER_LOCKED')
        updated = next(item for item in incoming if item['id'] == layer_id)
        if (
            updated['content'] != stored['content']
            or updated['reveal_at_chapter'] != stored['reveal_at_chapter']
            or updated['title'] != stored['title']
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='FROZEN_TRUTH_LAYER_LOCKED')

    before = {'truth_layers': existing}
    world.truth_layers = incoming
    commit_manual_world_change(
        db,
        world,
        object_type='truth_layer',
        object_id=world.id,
        action='updated',
        before=before,
        after={'truth_layers': incoming},
        edit_reason=edit_reason,
    )
    db.refresh(world)
    return world
