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
