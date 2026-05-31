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
    world = require_owned_world(db, user, world_id)
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


def _markdown_value(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    if isinstance(value, dict):
        return ', '.join(f'{key}: {item}' for key, item in value.items())
    return str(value)


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


def _world_markdown(payload: dict[str, Any], character_paths: dict[int, str], foreshadow_paths: dict[int, str], chapter_paths: dict[int, str]) -> str:
    world = payload['world']
    lines = [
        f"# {world['title']}",
        '',
        f"- Genre: {world['genre_template']}",
        f"- World Version: {world['world_version']}",
        f"- Truth Canon Version: {world['truth_canon_version']}",
        f"- Status: {world['status']}",
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
    lines.extend(['', '## Timeline', '', '- [[Timeline]]', ''])
    return '\n'.join(lines)


def _character_markdown(character: dict[str, Any], relations: list[dict[str, Any]], character_by_id: dict[int, dict[str, Any]], character_paths: dict[int, str]) -> str:
    character_id = character.get('id')
    related = [relation for relation in relations if character_id in {relation.get('source_character_id'), relation.get('target_character_id')}]
    lines = [
        f"# {character.get('name', f'Character {character_id}')}",
        '',
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


def _foreshadow_markdown(foreshadow: dict[str, Any], character_by_id: dict[int, dict[str, Any]], character_paths: dict[int, str]) -> str:
    related_character_lines = []
    for character_id in foreshadow.get('related_character_ids', []):
        name = _character_name(character_by_id, character_id)
        if character_id in character_paths:
            related_character_lines.append(f"[[{_wiki_path(character_paths[character_id])}]] {name}")
        else:
            related_character_lines.append(name)
    return '\n'.join(
        [
            f"# {foreshadow.get('title', f'Foreshadow {foreshadow.get("id")}')}",
            '',
            f"- Type: {foreshadow.get('foreshadow_type', '')}",
            f"- Status: {foreshadow.get('status', '')}",
            f"- Urgency: {foreshadow.get('urgency_level', '')}",
            f"- Source Chapter: {foreshadow.get('source_chapter_id') or ''}",
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
    lines = ['# Character Relations', '', '| Source | Target | Type | Intensity | Visibility |', '|---|---|---|---:|---|']
    for relation in relations:
        source_id = relation.get('source_character_id')
        target_id = relation.get('target_character_id')
        source_name = _character_name(character_by_id, source_id)
        target_name = _character_name(character_by_id, target_id)
        source = f"[[{_wiki_path(character_paths[source_id])}]] {source_name}" if source_id in character_paths else source_name
        target = f"[[{_wiki_path(character_paths[target_id])}]] {target_name}" if target_id in character_paths else target_name
        lines.append(
            f"| {source} | {target} | {relation.get('relation_type')} | {relation.get('intensity')} | {relation.get('visibility')} |"
        )
    return '\n'.join(lines) + '\n'


def _chapter_markdown(chapter: dict[str, Any], sequence: int) -> str:
    return '\n'.join(
        [
            f"# {chapter['title']}",
            '',
            f"- Chapter Number: {sequence}",
            f"- Chapter ID: {chapter['id']}",
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


def _events_markdown(events: list[dict[str, Any]]) -> str:
    lines = ['# Timeline', '', '## Event History', '', '| ID | Version | Type | Source | Chapter | Created |', '|---:|---|---|---|---|---|']
    lines.extend(
        f"| {event['id']} | {event['world_version_before']} → {event['world_version_after']} | {event['event_type']} | {event['source_type']} | {event.get('chapter_id') or ''} | {event['created_at']} |"
        for event in events
    )
    return '\n'.join(lines) + '\n'


def render_markdown_bundle(payload: dict[str, Any]) -> list[dict[str, str]]:
    used_paths = {'World.md', 'Relations.md', 'Timeline.md'}
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
    character_by_id = {character['id']: character for character in payload['characters']}

    files = [
        {'path': 'World.md', 'content': _world_markdown(payload, character_paths, foreshadow_paths, chapter_paths)},
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
            'content': _foreshadow_markdown(foreshadow, character_by_id, character_paths),
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
    files.append({'path': 'Timeline.md', 'content': _events_markdown(payload['events'])})
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
        'archive_base64': _zip_markdown_files(files),
        'files': files,
    }
