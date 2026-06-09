import base64
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
import re
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.event.models import EventLog
from app.narrative.models import Chapter
from app.snapshot_export.models import WorldSnapshot
from app.snapshot_export.schemas import WorldSnapshotCreate
from app.world.governance import require_owned_world_for_update
from app.world.models import World
from app.world.service import require_owned_world


def build_world_archive_payload(db: Session, world: World) -> dict:
    approved_chapters = list(
        db.scalars(
            select(Chapter)
            .where(Chapter.world_id == world.id)
            .where(Chapter.status == 'approved')
            .where(Chapter.approved_content.is_not(None))
            .where(Chapter.approved_version.is_not(None))
            .order_by(Chapter.id)
        )
    )
    events = list(db.scalars(select(EventLog).where(EventLog.world_id == world.id).order_by(EventLog.id)))
    return {
        'world': {
            'id': world.id,
            'title': world.title,
            'genre_template': world.genre_template,
            'truth_canon': world.truth_canon,
            'truth_canon_version': world.truth_canon_version,
            'world_version': world.world_version,
            'status': world.status,
            'tone_profile': deepcopy(world.tone_profile),
            'story_arc': deepcopy(world.story_arc),
        },
        'characters': deepcopy(world.current_characters),
        'relations': deepcopy(world.current_relations),
        'foreshadows': deepcopy(world.current_foreshadows),
        'approved_chapters': [
            {
                'id': chapter.id,
                'title': chapter.title,
                'status': chapter.status,
                'approved_version': chapter.approved_version,
                'base_world_version': chapter.base_world_version,
                'approved_content': chapter.approved_content,
            }
            for chapter in approved_chapters
        ],
        'events': [
            {
                'id': event.id,
                'chapter_id': event.chapter_id,
                'event_type': event.event_type,
                'source_type': event.source_type,
                'payload': deepcopy(event.payload),
                'world_version_before': event.world_version_before,
                'world_version_after': event.world_version_after,
                'created_at': event.created_at.isoformat(),
            }
            for event in events
        ],
    }


def create_world_snapshot(db: Session, user: User, world_id: int, data: WorldSnapshotCreate) -> WorldSnapshot:
    world = require_owned_world_for_update(db, user, world_id)
    snapshot = WorldSnapshot(
        world_id=world.id,
        world_version=world.world_version,
        label=data.label,
        note=data.note,
        payload=build_world_archive_payload(db, world),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def list_world_snapshots(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    snapshots = list(
        db.scalars(select(WorldSnapshot).where(WorldSnapshot.world_id == world.id).order_by(WorldSnapshot.id.desc()))
    )
    return {'world_id': world.id, 'snapshots': snapshots}


def get_world_snapshot_detail(db: Session, user: User, snapshot_id: int) -> WorldSnapshot:
    snapshot = db.get(WorldSnapshot, snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    require_owned_world(db, user, snapshot.world_id)
    return snapshot


WORLD_COMPARE_FIELDS = [
    'title',
    'genre_template',
    'truth_canon',
    'truth_canon_version',
    'world_version',
    'status',
    'tone_profile',
    'story_arc',
]


def _change_item(
    object_type: str,
    object_id: int | None,
    change_type: str,
    title: str,
    fields_changed: list[str],
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        'object_type': object_type,
        'object_id': object_id,
        'change_type': change_type,
        'title': title,
        'fields_changed': fields_changed,
        'before': before,
        'after': after,
    }


def _object_title(object_type: str, item: dict[str, Any] | None, fallback_id: int | None) -> str:
    if not item:
        return f'{object_type} {fallback_id or ""}'.strip()
    if object_type == 'character':
        return str(item.get('name') or f'Character {fallback_id}')
    if object_type == 'relation':
        return str(item.get('relation_type') or f'Relation {fallback_id}')
    if object_type == 'foreshadow':
        return str(item.get('title') or f'Foreshadow {fallback_id}')
    if object_type == 'chapter':
        return str(item.get('title') or f'Chapter {fallback_id}')
    if object_type == 'event':
        return str(item.get('event_type') or f'Event {fallback_id}')
    return str(item.get('title') or f'{object_type} {fallback_id}')


def _index_by_id(items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(item['id']): item for item in items if item.get('id') is not None}


def _diff_world(base_payload: dict[str, Any], target_payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_world = base_payload.get('world') or {}
    target_world = target_payload.get('world') or {}
    fields_changed = [field for field in WORLD_COMPARE_FIELDS if base_world.get(field) != target_world.get(field)]
    if not fields_changed:
        return []
    return [
        _change_item(
            'world',
            None,
            'changed',
            str(target_world.get('title') or base_world.get('title') or 'World'),
            fields_changed,
            {field: base_world.get(field) for field in fields_changed},
            {field: target_world.get(field) for field in fields_changed},
        )
    ]


def _diff_collection(
    base_payload: dict[str, Any],
    target_payload: dict[str, Any],
    payload_key: str,
    object_type: str,
) -> list[dict[str, Any]]:
    base_by_id = _index_by_id(base_payload.get(payload_key) or [])
    target_by_id = _index_by_id(target_payload.get(payload_key) or [])
    changes: list[dict[str, Any]] = []
    for object_id in sorted(set(base_by_id) | set(target_by_id)):
        before = base_by_id.get(object_id)
        after = target_by_id.get(object_id)
        if before is None and after is not None:
            changes.append(_change_item(object_type, object_id, 'added', _object_title(object_type, after, object_id), [], None, after))
            continue
        if before is not None and after is None:
            changes.append(_change_item(object_type, object_id, 'removed', _object_title(object_type, before, object_id), [], before, None))
            continue
        if before is None or after is None or before == after:
            continue
        fields_changed = sorted({key for key in set(before) | set(after) if before.get(key) != after.get(key)})
        changes.append(
            _change_item(
                object_type,
                object_id,
                'changed',
                _object_title(object_type, after, object_id),
                fields_changed,
                before,
                after,
            )
        )
    return changes


def compare_world_snapshots(db: Session, user: User, base_snapshot_id: int, target_snapshot_id: int) -> dict[str, Any]:
    base_snapshot = db.get(WorldSnapshot, base_snapshot_id)
    if base_snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    require_owned_world(db, user, base_snapshot.world_id)

    target_snapshot = db.get(WorldSnapshot, target_snapshot_id)
    if target_snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if target_snapshot.world_id != base_snapshot.world_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')

    base_payload = base_snapshot.payload or {}
    target_payload = target_snapshot.payload or {}
    changes = {
        'world': _diff_world(base_payload, target_payload),
        'characters': _diff_collection(base_payload, target_payload, 'characters', 'character'),
        'relations': _diff_collection(base_payload, target_payload, 'relations', 'relation'),
        'foreshadows': _diff_collection(base_payload, target_payload, 'foreshadows', 'foreshadow'),
        'chapters': _diff_collection(base_payload, target_payload, 'approved_chapters', 'chapter'),
        'events': _diff_collection(base_payload, target_payload, 'events', 'event'),
    }
    object_type_counts: dict[str, int] = {}
    for items in changes.values():
        for item in items:
            object_type_counts[item['object_type']] = object_type_counts.get(item['object_type'], 0) + 1
    return {
        'world_id': base_snapshot.world_id,
        'base_snapshot': base_snapshot,
        'target_snapshot': target_snapshot,
        'summary': {
            'total_changes': sum(object_type_counts.values()),
            'object_type_counts': object_type_counts,
        },
        'changes': changes,
    }


def _markdown_value(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    if isinstance(value, dict):
        return ', '.join(f'{key}: {item}' for key, item in value.items())
    return str(value)


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    if re.fullmatch(r'[\w一-鿿./-]+', text, flags=re.UNICODE):
        return text
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def _frontmatter(data: dict[str, Any]) -> str:
    lines = ['---']
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f'{key}: []')
                continue
            lines.append(f'{key}:')
            lines.extend(f'  - {_yaml_scalar(item)}' for item in value)
        else:
            lines.append(f'{key}: {_yaml_scalar(value)}')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def _markdown_cell(value: Any) -> str:
    return _markdown_value(value).replace('\n', ' ').replace('|', '\\|') or '暂无'


def _safe_segment(value: str | None, fallback: str) -> str:
    base = (value or fallback).strip() or fallback
    segment = re.sub(r'[^\w一-鿿.-]+', '-', base, flags=re.UNICODE).strip('-.')
    return segment or fallback


def _unique_markdown_path(directory: str, value: str | None, fallback: str, used_paths: set[str]) -> str:
    stem = _safe_segment(value, fallback)
    suffix = 1
    while True:
        candidate_stem = stem if suffix == 1 else f'{stem}-{suffix}'
        path = f'{directory}/{candidate_stem}.md'
        if path not in used_paths:
            used_paths.add(path)
            return path
        suffix += 1


def _wiki_path(path: str) -> str:
    return path.removesuffix('.md')


def _character_name(character_by_id: dict[int, dict[str, Any]], character_id: int | None) -> str:
    character = character_by_id.get(character_id or -1)
    return character.get('name') if character else str(character_id or '')


def _world_markdown(
    payload: dict[str, Any],
    character_paths: dict[int, str],
    foreshadow_paths: dict[int, str],
    chapter_paths: dict[int, str],
    event_paths: dict[int, str],
) -> str:
    world = payload['world']
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'world_index',
                'world_id': world['id'],
                'world_version': world['world_version'],
                'truth_canon_version': world['truth_canon_version'],
                'status': world['status'],
                'title': world['title'],
                'tags': ['worldsim/world'],
            }
        ),
        f"# {world['title']}",
        '',
        f"- Genre: {world['genre_template']}",
        f"- World Version: {world['world_version']}",
        f"- Truth Canon Version: {world['truth_canon_version']}",
        f"- Status: {world['status']}",
        '',
        '## Vault Navigation',
        '',
        '- [[README]]',
        '- [[Manifest]]',
        '- [[Story Bible]]',
        '- [[Relations]]',
        '- [[Timeline]]',
        '- [[Indexes/Characters]]',
        '- [[Indexes/Foreshadows]]',
        '- [[Indexes/Chapters]]',
        '- [[Indexes/Timeline]]',
        '- [[Indexes/Events]]',
        '',
        '## Truth Canon',
        '',
        world['truth_canon'],
        '',
        '## Story Arc',
        '',
    ]
    story_arc = world.get('story_arc') or []
    lines.extend(f"- {_markdown_value(item)}" for item in story_arc) if story_arc else lines.append('- 暂无')
    lines.extend(['', '## Characters', ''])
    lines.extend(
        f"- [[{_wiki_path(character_paths[character['id']])}]] {character.get('name', '')}"
        for character in payload['characters']
        if character.get('id') in character_paths
    )
    lines.extend(['', '## Foreshadows', ''])
    lines.extend(
        f"- [[{_wiki_path(foreshadow_paths[foreshadow['id']])}]] {foreshadow.get('title', '')}"
        for foreshadow in payload['foreshadows']
        if foreshadow.get('id') in foreshadow_paths
    )
    lines.extend(['', '## Approved Chapters', ''])
    if payload['approved_chapters']:
        lines.extend(
            f"- [[{_wiki_path(chapter_paths[chapter['id']])}]] {chapter['title']}"
            for chapter in payload['approved_chapters']
            if chapter.get('id') in chapter_paths
        )
    else:
        lines.append('- 暂无')
    lines.extend(['', '## Timeline', '', '- [[Timeline]]', '- [[Indexes/Events]]'])
    if payload['events']:
        lines.extend(
            f"- [[{_wiki_path(event_paths[event['id']])}]] {event.get('event_type', '')}"
            for event in payload['events'][:5]
            if event.get('id') in event_paths
        )
    lines.append('')
    return '\n'.join(lines)


def _character_markdown(character: dict[str, Any], relations: list[dict[str, Any]], character_by_id: dict[int, dict[str, Any]], character_paths: dict[int, str]) -> str:
    character_id = character.get('id')
    related = [relation for relation in relations if character_id in {relation.get('source_character_id'), relation.get('target_character_id')}]
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'character',
                'character_id': character_id,
                'name': character.get('name'),
                'role': character.get('role_type'),
                'status': character.get('status'),
                'destiny_flag': character.get('destiny_flag'),
                'tags': ['worldsim/character'],
            }
        ),
        f"# {character.get('name', f'Character {character_id}')}",
        '',
        '- World: [[World]]',
        f"- Role: {character.get('role_type', '')}",
        f"- Status: {character.get('status', '')}",
        f"- Destiny Flag: {character.get('destiny_flag') or ''}",
        f"- Current Goals: {_markdown_value(character.get('current_goals', []))}",
        '',
        '## Public Profile',
        '',
        _markdown_value(character.get('public_profile', {})) or '暂无',
        '',
        '## Hidden Traits',
        '',
        _markdown_value(character.get('hidden_traits', {})) or '暂无',
        '',
        '## Relations',
        '',
    ]
    if related:
        for relation in related:
            source_id = relation.get('source_character_id')
            target_id = relation.get('target_character_id')
            source_name = _character_name(character_by_id, source_id)
            target_name = _character_name(character_by_id, target_id)
            source_link = f"[[{_wiki_path(character_paths[source_id])}]]" if source_id in character_paths else source_name
            target_link = f"[[{_wiki_path(character_paths[target_id])}]]" if target_id in character_paths else target_name
            lines.append(
                f"- {source_link} {source_name} → {target_link} {target_name}: {relation.get('relation_type')} "
                f"(intensity {relation.get('intensity')}, {relation.get('visibility')})"
            )
    else:
        lines.append('- 暂无')
    return '\n'.join(lines) + '\n'


def _foreshadow_markdown(
    foreshadow: dict[str, Any],
    character_by_id: dict[int, dict[str, Any]],
    character_paths: dict[int, str],
    chapter_paths: dict[int, str],
) -> str:
    related_character_lines = []
    for character_id in foreshadow.get('related_character_ids', []):
        name = _character_name(character_by_id, character_id)
        if character_id in character_paths:
            related_character_lines.append(f"[[{_wiki_path(character_paths[character_id])}]] {name}")
        else:
            related_character_lines.append(name)
    source_chapter_link = _foreshadow_source_chapter_link(foreshadow, chapter_paths)
    return '\n'.join(
        [
            _frontmatter(
                {
                    'worldsim_type': 'foreshadow',
                    'foreshadow_id': foreshadow.get('id'),
                    'title': foreshadow.get('title'),
                    'status': foreshadow.get('status'),
                    'urgency': foreshadow.get('urgency_level'),
                    'source_chapter_id': foreshadow.get('source_chapter_id'),
                    'related_character_ids': foreshadow.get('related_character_ids', []),
                    'tags': ['worldsim/foreshadow'],
                }
            ),
            f"# {foreshadow.get('title', f'Foreshadow {foreshadow.get("id")}')}",
            '',
            '- World: [[World]]',
            f"- Type: {foreshadow.get('foreshadow_type', '')}",
            f"- Status: {foreshadow.get('status', '')}",
            f"- Urgency: {foreshadow.get('urgency_level', '')}",
            f"- Source Chapter: {source_chapter_link}",
            f"- Related Characters: {_markdown_value(related_character_lines)}",
            f"- Expected Resolution: {foreshadow.get('expected_resolution_window') or ''}",
            '',
            '## Description',
            '',
            foreshadow.get('description', ''),
            '',
        ]
    )


def _relations_markdown(relations: list[dict[str, Any]], character_by_id: dict[int, dict[str, Any]], character_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'relations',
                'relation_count': len(relations),
                'tags': ['worldsim/relations'],
            }
        ),
        '# Character Relations',
        '',
        '- World: [[World]]',
        '',
        '| Source | Target | Type | Intensity | Visibility |',
        '|---|---|---|---:|---|',
    ]
    for relation in relations:
        source_id = relation.get('source_character_id')
        target_id = relation.get('target_character_id')
        source_name = _character_name(character_by_id, source_id)
        target_name = _character_name(character_by_id, target_id)
        source = f"[[{_wiki_path(character_paths[source_id])}]] {source_name}" if source_id in character_paths else source_name
        target = f"[[{_wiki_path(character_paths[target_id])}]] {target_name}" if target_id in character_paths else target_name
        lines.append(
            f"| {_markdown_cell(source)} | {_markdown_cell(target)} | {_markdown_cell(relation.get('relation_type'))} | {relation.get('intensity')} | {_markdown_cell(relation.get('visibility'))} |"
        )
    return '\n'.join(lines) + '\n'


def _chapter_markdown(chapter: dict[str, Any], sequence: int) -> str:
    return '\n'.join(
        [
            _frontmatter(
                {
                    'worldsim_type': 'chapter',
                    'chapter_id': chapter['id'],
                    'title': chapter['title'],
                    'status': chapter['status'],
                    'approved_version': chapter['approved_version'],
                    'base_world_version': chapter['base_world_version'],
                    'chapter_number': sequence,
                    'tags': ['worldsim/chapter'],
                }
            ),
            f"# {chapter['title']}",
            '',
            '- World: [[World]]',
            f"- Chapter Number: {sequence}",
            f"- Status: {chapter['status']}",
            f"- Approved Version: {chapter['approved_version']}",
            f"- Base World Version: {chapter['base_world_version']}",
            '',
            '## Content',
            '',
            chapter.get('approved_content') or '',
            '',
        ]
    )


def _foreshadow_source_chapter_link(foreshadow: dict[str, Any], chapter_paths: dict[int, str]) -> str:
    source_chapter_id = foreshadow.get('source_chapter_id')
    if source_chapter_id in chapter_paths:
        return f"[[{_wiki_path(chapter_paths[source_chapter_id])}]]"
    return str(source_chapter_id or '')


def _event_chapter_link(event: dict[str, Any], chapter_paths: dict[int, str]) -> str:
    chapter_id = event.get('chapter_id')
    return f"[[{_wiki_path(chapter_paths[chapter_id])}]]" if chapter_id in chapter_paths else ''


def _events_markdown(events: list[dict[str, Any]], event_paths: dict[int, str], chapter_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'timeline',
                'event_count': len(events),
                'tags': ['worldsim/timeline'],
            }
        ),
        '# Timeline',
        '',
        '- World: [[World]]',
        '- Event Index: [[Indexes/Events]]',
        '',
        '## Summary',
        '',
        f'- Event Count: {len(events)}',
        '',
        '## Event History',
        '',
        '| Event | Version | Type | Source | Chapter | Created |',
        '|---|---|---|---|---|---|',
    ]
    lines.extend(
        f"| [[{_wiki_path(event_paths[event['id']])}]] | {event['world_version_before']} → {event['world_version_after']} | {_markdown_cell(event['event_type'])} | {_markdown_cell(event['source_type'])} | {_event_chapter_link(event, chapter_paths)} | {event['created_at']} |"
        for event in events
        if event.get('id') in event_paths
    )
    return '\n'.join(lines) + '\n'


def _story_bible_markdown(payload: dict[str, Any]) -> str:
    world = payload['world']
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'story_bible',
                'world_id': world['id'],
                'world_version': world['world_version'],
                'truth_canon_version': world['truth_canon_version'],
                'title': world['title'],
                'tags': ['worldsim/story-bible'],
            }
        ),
        '# Story Bible',
        '',
        '- World: [[World]]',
        '- Characters: [[Indexes/Characters]]',
        '- Foreshadows: [[Indexes/Foreshadows]]',
        '',
        '## Truth Canon',
        '',
        world['truth_canon'] or '暂无',
        '',
        '## Story Arc',
        '',
    ]
    story_arc = world.get('story_arc') or []
    lines.extend(f"- {_markdown_value(item)}" for item in story_arc) if story_arc else lines.append('- 暂无')
    lines.append('')
    return '\n'.join(lines)


def _is_internal_payload_key(key: str) -> bool:
    return key == 'commit_group_id' or key.endswith('_id') or key.endswith('_ids')


def _scrub_event_payload_value(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, nested_value in value.items():
            if _is_internal_payload_key(str(key)):
                continue
            scrubbed = _scrub_event_payload_value(nested_value)
            if scrubbed in ({}, []):
                continue
            cleaned[key] = scrubbed
        return cleaned
    if isinstance(value, list):
        cleaned_items = []
        for item in value:
            scrubbed = _scrub_event_payload_value(item)
            if scrubbed in ({}, []):
                continue
            cleaned_items.append(scrubbed)
        return cleaned_items
    return value


def _event_payload_lines(payload: dict[str, Any]) -> list[str]:
    lines = []
    for key, value in payload.items():
        if _is_internal_payload_key(str(key)):
            continue
        scrubbed = _scrub_event_payload_value(value)
        if scrubbed in ({}, []):
            continue
        lines.append(f"- {key}: {_markdown_value(scrubbed)}")
    return lines or ['- 暂无']


def _event_markdown(event: dict[str, Any], sequence: int, chapter_paths: dict[int, str]) -> str:
    chapter_link = _event_chapter_link(event, chapter_paths) or '无关联章节'
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'event',
                'event_id': event['id'],
                'event_number': sequence,
                'event_type': event['event_type'],
                'source_type': event['source_type'],
                'world_version_before': event['world_version_before'],
                'world_version_after': event['world_version_after'],
                'tags': ['worldsim/event'],
            }
        ),
        f"# Event {sequence:03d}: {event['event_type']}",
        '',
        '- World: [[World]]',
        f'- Related Chapter: {chapter_link}',
        f"- World Version: {event['world_version_before']} → {event['world_version_after']}",
        f"- Source: {event['source_type']}",
        f"- Created: {event['created_at']}",
        '',
        '## Details',
        '',
    ]
    lines.extend(_event_payload_lines(event.get('payload') or {}))
    lines.append('')
    return '\n'.join(lines)


def _readme_markdown(payload: dict[str, Any]) -> str:
    world = payload['world']
    return _frontmatter(
        {
            'worldsim_type': 'vault_readme',
            'world_id': world['id'],
            'world_version': world['world_version'],
            'title': world['title'],
            'tags': ['worldsim/readme'],
        }
    ) + '\n'.join(
        [
            f"# {world['title']} Markdown Vault",
            '',
            'Open [[World]] first.',
            '',
            '## Main files',
            '',
            '- [[World]] — canonical world overview and vault index.',
            '- [[Manifest]] — vault file inventory and archive verification notes.',
            '- [[Story Bible]] — canon and story arc reference.',
            '- [[Relations]] — character relationship table.',
            '- [[Timeline]] — event history exported from WorldSim.',
            '- [[Indexes/Characters]] — character directory.',
            '- [[Indexes/Foreshadows]] — foreshadow ledger directory.',
            '- [[Indexes/Chapters]] — approved chapter directory.',
            '- [[Indexes/Timeline]] — timeline helper page.',
            '- [[Indexes/Events]] — event note directory.',
            '',
            'The original API contract is preserved: this vault is also returned as inline `files` and a base64 ZIP archive.',
            '',
        ]
    )


def _manifest_markdown(payload: dict[str, Any], files: list[dict[str, str]]) -> str:
    world = payload['world']
    file_paths = [file['path'] for file in files]
    archive_fallback = f"World-{world['id']}"
    archive_filename = f"WorldSim-{_safe_segment(world['title'], archive_fallback)}-v{world['world_version']}-markdown.zip"
    lines = [
        _frontmatter(
            {
                'worldsim_type': 'vault_manifest',
                'world_id': world['id'],
                'world_version': world['world_version'],
                'file_count': len(file_paths),
                'tags': ['worldsim/manifest'],
            }
        ),
        '# Vault Manifest',
        '',
        '- World: [[World]]',
        '- README: [[README]]',
        '',
        '## Archive Metadata',
        '',
        f'- archive_filename: {archive_filename}',
        '- archive_format: zip',
        '- archive_encoding: base64',
        '- files_are_inline: true',
        '',
        '## Content Counts',
        '',
        f"- Characters: {len(payload['characters'])}",
        f"- Relations: {len(payload['relations'])}",
        f"- Foreshadows: {len(payload['foreshadows'])}",
        f"- Approved Chapters: {len(payload['approved_chapters'])}",
        f"- Events: {len(payload['events'])}",
        f'- Files: {len(file_paths)}',
        '',
        '## Preserved API Contract',
        '',
        '- archive_format: zip',
        '- archive_encoding: base64',
        '- archive_base64: present in API response',
        '- files_are_inline: true',
        '- files: inline preview entries match ZIP paths',
        '',
        '## File Inventory',
        '',
    ]
    lines.extend(f"- [[{_wiki_path(path)}]] `{path}`" for path in file_paths if path.endswith('.md'))
    lines.append('')
    return '\n'.join(lines)


def _characters_index_markdown(characters: list[dict[str, Any]], character_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter({'worldsim_type': 'character_index', 'character_count': len(characters), 'tags': ['worldsim/index', 'worldsim/character']}),
        '# Characters Index',
        '',
        '- World: [[World]]',
        '',
        '| Character | Role | Status | Goals |',
        '|---|---|---|---|',
    ]
    for character in characters:
        character_id = character.get('id')
        link = f"[[{_wiki_path(character_paths[character_id])}]]" if character_id in character_paths else _markdown_cell(character.get('name'))
        lines.append(
            f"| {link} | {_markdown_cell(character.get('role_type'))} | {_markdown_cell(character.get('status'))} | {_markdown_cell(character.get('current_goals', []))} |"
        )
    return '\n'.join(lines) + '\n'


def _foreshadows_index_markdown(foreshadows: list[dict[str, Any]], foreshadow_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter({'worldsim_type': 'foreshadow_index', 'foreshadow_count': len(foreshadows), 'tags': ['worldsim/index', 'worldsim/foreshadow']}),
        '# Foreshadows Index',
        '',
        '- World: [[World]]',
        '',
        '| Foreshadow | Type | Status | Urgency | Expected Resolution |',
        '|---|---|---|---:|---|',
    ]
    for foreshadow in foreshadows:
        foreshadow_id = foreshadow.get('id')
        link = f"[[{_wiki_path(foreshadow_paths[foreshadow_id])}]]" if foreshadow_id in foreshadow_paths else _markdown_cell(foreshadow.get('title'))
        lines.append(
            f"| {link} | {_markdown_cell(foreshadow.get('foreshadow_type'))} | {_markdown_cell(foreshadow.get('status'))} | {foreshadow.get('urgency_level') or ''} | {_markdown_cell(foreshadow.get('expected_resolution_window'))} |"
        )
    return '\n'.join(lines) + '\n'


def _chapters_index_markdown(chapters: list[dict[str, Any]], chapter_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter({'worldsim_type': 'chapter_index', 'chapter_count': len(chapters), 'tags': ['worldsim/index', 'worldsim/chapter']}),
        '# Approved Chapters Index',
        '',
        '- World: [[World]]',
        '',
        '| Chapter | Status | Approved Version | Base World Version |',
        '|---|---|---:|---:|',
    ]
    for chapter in chapters:
        chapter_id = chapter.get('id')
        link = f"[[{_wiki_path(chapter_paths[chapter_id])}]]" if chapter_id in chapter_paths else _markdown_cell(chapter.get('title'))
        lines.append(
            f"| {link} | {_markdown_cell(chapter.get('status'))} | {chapter.get('approved_version') or ''} | {chapter.get('base_world_version') or ''} |"
        )
    if not chapters:
        lines.append('| 暂无 |  |  |  |')
    return '\n'.join(lines) + '\n'


def _timeline_index_markdown(events: list[dict[str, Any]], event_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter({'worldsim_type': 'timeline_index', 'event_count': len(events), 'tags': ['worldsim/index', 'worldsim/timeline']}),
        '# Timeline Index',
        '',
        '- World: [[World]]',
        '- Event History: [[Timeline]]',
        '- Event Notes: [[Indexes/Events]]',
        f'- Event Count: {len(events)}',
        '',
    ]
    lines.extend(
        f"- [[{_wiki_path(event_paths[event['id']])}]] {event.get('event_type', '')}"
        for event in events
        if event.get('id') in event_paths
    )
    lines.append('')
    return '\n'.join(lines)


def _events_index_markdown(events: list[dict[str, Any]], event_paths: dict[int, str]) -> str:
    lines = [
        _frontmatter({'worldsim_type': 'event_index', 'event_count': len(events), 'tags': ['worldsim/index', 'worldsim/event']}),
        '# Events Index',
        '',
        '- World: [[World]]',
        '- Timeline: [[Timeline]]',
        '',
        '| Event | Version | Type | Source | Created |',
        '|---|---|---|---|---|',
    ]
    lines.extend(
        f"| [[{_wiki_path(event_paths[event['id']])}]] | {event['world_version_before']} → {event['world_version_after']} | {_markdown_cell(event['event_type'])} | {_markdown_cell(event['source_type'])} | {event['created_at']} |"
        for event in events
        if event.get('id') in event_paths
    )
    return '\n'.join(lines) + '\n'


def render_markdown_bundle(payload: dict[str, Any]) -> list[dict[str, str]]:
    used_paths = {'World.md', 'Manifest.md', 'Story Bible.md', 'Relations.md', 'Timeline.md', 'README.md'}
    character_paths = {
        character['id']: _unique_markdown_path('Characters', character.get('name'), f"Character-{character.get('id')}", used_paths)
        for character in payload['characters']
    }
    foreshadow_paths = {
        foreshadow['id']: _unique_markdown_path('Foreshadows', foreshadow.get('title'), f"Foreshadow-{foreshadow.get('id')}", used_paths)
        for foreshadow in payload['foreshadows']
    }
    chapter_paths = {
        chapter['id']: f'Chapters/Chapter-{index:03d}.md'
        for index, chapter in enumerate(payload['approved_chapters'], start=1)
    }
    event_paths = {
        event['id']: f'Events/Event-{index:03d}.md'
        for index, event in enumerate(payload['events'], start=1)
    }
    character_by_id = {character['id']: character for character in payload['characters']}

    files = [
        {'path': 'World.md', 'content': _world_markdown(payload, character_paths, foreshadow_paths, chapter_paths, event_paths)},
        {'path': 'Story Bible.md', 'content': _story_bible_markdown(payload)},
        {'path': 'Relations.md', 'content': _relations_markdown(payload['relations'], character_by_id, character_paths)},
    ]
    files.extend(
        {
            'path': character_paths[character['id']],
            'content': _character_markdown(character, payload['relations'], character_by_id, character_paths),
        }
        for character in payload['characters']
    )
    files.extend(
        {
            'path': foreshadow_paths[foreshadow['id']],
            'content': _foreshadow_markdown(foreshadow, character_by_id, character_paths, chapter_paths),
        }
        for foreshadow in payload['foreshadows']
    )
    files.extend(
        {
            'path': chapter_paths[chapter['id']],
            'content': _chapter_markdown(chapter, index),
        }
        for index, chapter in enumerate(payload['approved_chapters'], start=1)
    )
    files.extend(
        {
            'path': event_paths[event['id']],
            'content': _event_markdown(event, index, chapter_paths),
        }
        for index, event in enumerate(payload['events'], start=1)
    )
    files.append({'path': 'Timeline.md', 'content': _events_markdown(payload['events'], event_paths, chapter_paths)})
    files.extend(
        [
            {'path': 'README.md', 'content': _readme_markdown(payload)},
            {'path': 'Indexes/Characters.md', 'content': _characters_index_markdown(payload['characters'], character_paths)},
            {'path': 'Indexes/Foreshadows.md', 'content': _foreshadows_index_markdown(payload['foreshadows'], foreshadow_paths)},
            {'path': 'Indexes/Chapters.md', 'content': _chapters_index_markdown(payload['approved_chapters'], chapter_paths)},
            {'path': 'Indexes/Timeline.md', 'content': _timeline_index_markdown(payload['events'], event_paths)},
            {'path': 'Indexes/Events.md', 'content': _events_index_markdown(payload['events'], event_paths)},
        ]
    )
    manifest_file = {'path': 'Manifest.md', 'content': ''}
    manifest_file['content'] = _manifest_markdown(payload, [*files, manifest_file])
    files.append(manifest_file)
    return files


def _zip_markdown_files(files: list[dict[str, str]]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, mode='w', compression=ZIP_DEFLATED) as archive:
        for file in files:
            archive.writestr(file['path'], file['content'])
    return base64.b64encode(buffer.getvalue()).decode('ascii')


def _archive_filename(world: World) -> str:
    return f"WorldSim-{_safe_segment(world.title, f'World-{world.id}')}-v{world.world_version}-markdown.zip"


def export_world_markdown(db: Session, user: User, world_id: int) -> dict[str, Any]:
    world = require_owned_world(db, user, world_id)
    payload = build_world_archive_payload(db, world)
    files = render_markdown_bundle(payload)
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'generated_at': datetime.now(timezone.utc),
        'archive_filename': _archive_filename(world),
        'archive_format': 'zip',
        'archive_encoding': 'base64',
        'archive_base64': _zip_markdown_files(files),
        'files_are_inline': True,
        'files': files,
    }
