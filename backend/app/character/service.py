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


def get_characters(
    db: Session,
    user: User,
    world_id: int,
    statuses: list[str] | None = None,
    role_types: list[str] | None = None,
    destiny_flags: list[str] | None = None,
) -> list[Character]:
    require_owned_world(db, user, world_id)
    stmt = select(Character).where(Character.world_id == world_id)
    if statuses:
        stmt = stmt.where(Character.status.in_(statuses))
    if role_types:
        stmt = stmt.where(Character.role_type.in_(role_types))
    if destiny_flags:
        stmt = stmt.where(Character.destiny_flag.in_(destiny_flags))
    return list(db.scalars(stmt.order_by(Character.id)))


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


def batch_update_characters(
    db: Session,
    user: User,
    world_id: int,
    operations: list,
) -> list[Character]:
    """Apply a batch of simple character governance operations."""
    world = require_owned_world_for_update(db, user, world_id)
    updated = []
    for op in operations:
        character = db.get(Character, op.character_id)
        if character is None or character.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='CHARACTER_NOT_FOUND')
        before = character_projection(character)
        if op.action == 'archive':
            character.status = 'archived'
        elif op.action == 'activate':
            character.status = 'active'
        elif op.action == 'set_destiny':
            if not op.value or not op.value.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='VALUE_REQUIRED')
            character.destiny_flag = op.value.strip()
        elif op.action == 'tag':
            if not op.value or not op.value.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='VALUE_REQUIRED')
            profile = dict(character.public_profile or {})
            tags = profile.get('tags') or []
            tag = op.value.strip()
            if tag not in tags:
                tags.append(tag)
            profile['tags'] = tags
            character.public_profile = profile
        after = character_projection(character)
        commit_manual_world_change(
            db,
            world,
            object_type='character',
            object_id=character.id,
            action=f'batch_{op.action}',
            before=before,
            after=after,
            edit_reason='批量资料治理操作',
        )
        updated.append(character)
    return updated


def detect_world_anomalies(db: Session, user: User, world_id: int) -> list[dict]:
    """Detect common data-governance anomalies in a world."""
    world = require_owned_world(db, user, world_id)
    anomalies = []

    characters = list(
        db.scalars(
            select(Character).where(Character.world_id == world_id).order_by(Character.id)
        )
    )
    character_ids = {ch.id for ch in characters}

    # 1. Duplicate character names
    name_counts: dict[str, int] = {}
    for ch in characters:
        name_counts[ch.name] = name_counts.get(ch.name, 0) + 1
    for name, count in name_counts.items():
        if count > 1:
            anomalies.append({
                'kind': 'duplicate_character_name',
                'severity': 'warning',
                'detail': f'角色名 "{name}" 出现 {count} 次',
                'object_type': 'character',
                'object_id': None,
            })

    # 2. Broken relations
    from app.character.models import CharacterRelation
    relations = list(
        db.scalars(
            select(CharacterRelation).where(CharacterRelation.world_id == world_id)
        )
    )
    for rel in relations:
        missing = []
        if rel.source_character_id not in character_ids:
            missing.append('source')
        if rel.target_character_id not in character_ids:
            missing.append('target')
        if missing:
            anomalies.append({
                'kind': 'broken_relation',
                'severity': 'critical',
                'detail': f'关系 {rel.id} 指向不存在的角色（{"、".join(missing)}）',
                'object_type': 'relation',
                'object_id': rel.id,
            })

    # 3. Stale foreshadows: past window but still planted/advanced
    from app.foreshadow.models import Foreshadow
    foreshadows = list(
        db.scalars(
            select(Foreshadow).where(Foreshadow.world_id == world_id)
        )
    )
    approved_chapter_count = _approved_chapter_count(db, world_id)
    import re as _re
    for f in foreshadows:
        window = f.expected_resolution_window or ''
        m = _re.match(r'第(\d+)-(\d+)章', window)
        if not m:
            continue
        win_end = int(m.group(2))
        if approved_chapter_count > win_end and f.status in ('planted', 'advanced'):
            anomalies.append({
                'kind': 'stale_foreshadow',
                'severity': 'warning',
                'detail': f'伏笔 "{f.title}" 已超出解析窗口（第{win_end}章），当前状态仍为 {f.status}',
                'object_type': 'foreshadow',
                'object_id': f.id,
            })

    # 4. Character with no goals and no public identity
    for ch in characters:
        profile = ch.public_profile or {}
        if not (ch.current_goals) and not profile.get('identity'):
            anomalies.append({
                'kind': 'empty_character',
                'severity': 'info',
                'detail': f'角色 "{ch.name}" 没有当前目标，public_profile 也缺少 identity',
                'object_type': 'character',
                'object_id': ch.id,
            })

    return anomalies


def _approved_chapter_count(db: Session, world_id: int) -> int:
    """Count approved chapters in a world."""
    from sqlalchemy import func
    from app.narrative.models import Chapter
    return db.scalar(
        select(func.count()).select_from(Chapter).where(
            Chapter.world_id == world_id,
            Chapter.approved_version.is_not(None),
        )
    ) or 0
