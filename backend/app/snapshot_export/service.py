from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any

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


def _slug(value: str | None, fallback: str) -> str:
    base = (value or fallback).strip() or fallback
    slug = re.sub(r'[^\w一-鿿.-]+', '-', base, flags=re.UNICODE).strip('-')
    return slug or fallback


def _world_markdown(payload: dict[str, Any]) -> str:
    world = payload['world']
    lines = [
        f"# {world['title']}",
        '',
        f"- Genre: {world['genre_template']}",
        f"- World Version: {world['world_version']}",
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
    lines.extend(f"- [[Characters/{_slug(character.get('name'), f'Character-{character.get("id")}')}]]" for character in payload['characters'])
    lines.extend(['', '## Foreshadows', ''])
    lines.extend(f"- [[Foreshadows/{_slug(foreshadow.get('title'), f'Foreshadow-{foreshadow.get("id")}')}]]" for foreshadow in payload['foreshadows'])
    lines.extend(['', '## Approved Chapters', ''])
    lines.extend(f"- [[Chapters/Chapter-{chapter['id']}]] {chapter['title']}" for chapter in payload['approved_chapters'])
    lines.extend(['', '## Timeline', '', '- [[Timeline/Events]]', ''])
    return '\n'.join(lines)


def _character_markdown(character: dict[str, Any], relations: list[dict[str, Any]]) -> str:
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
        '## Relations',
        '',
    ]
    lines.extend(
        f"- {relation.get('source_character_id')} → {relation.get('target_character_id')}: {relation.get('relation_type')} "
        f"(intensity {relation.get('intensity')}, {relation.get('visibility')})"
        for relation in related
    ) if related else lines.append('- 暂无')
    return '\n'.join(lines) + '\n'


def _foreshadow_markdown(foreshadow: dict[str, Any]) -> str:
    return '\n'.join(
        [
            f"# {foreshadow.get('title', f'Foreshadow {foreshadow.get("id")}')}",
            '',
            f"- Type: {foreshadow.get('foreshadow_type', '')}",
            f"- Status: {foreshadow.get('status', '')}",
            f"- Urgency: {foreshadow.get('urgency_level', '')}",
            f"- Related Characters: {_markdown_value(foreshadow.get('related_character_ids', []))}",
            f"- Expected Resolution: {foreshadow.get('expected_resolution_window') or ''}",
            '',
            '## Description',
            '',
            foreshadow.get('description', ''),
            '',
        ]
    )


def _relations_markdown(relations: list[dict[str, Any]]) -> str:
    lines = ['# Character Relations', '', '| Source | Target | Type | Intensity | Visibility |', '|---|---|---|---:|---|']
    lines.extend(
        f"| {relation.get('source_character_id')} | {relation.get('target_character_id')} | {relation.get('relation_type')} | {relation.get('intensity')} | {relation.get('visibility')} |"
        for relation in relations
    )
    return '\n'.join(lines) + '\n'


def _chapter_markdown(chapter: dict[str, Any]) -> str:
    return '\n'.join(
        [
            f"# {chapter['title']}",
            '',
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
    lines = ['# Event Timeline', '', '| ID | Version | Type | Source | Chapter | Created |', '|---:|---|---|---|---|---|']
    lines.extend(
        f"| {event['id']} | {event['world_version_before']} → {event['world_version_after']} | {event['event_type']} | {event['source_type']} | {event.get('chapter_id') or ''} | {event['created_at']} |"
        for event in events
    )
    return '\n'.join(lines) + '\n'


def render_markdown_bundle(payload: dict[str, Any]) -> list[dict[str, str]]:
    files = [
        {'path': 'World.md', 'content': _world_markdown(payload)},
        {'path': 'Relations.md', 'content': _relations_markdown(payload['relations'])},
    ]
    files.extend(
        {
            'path': f"Characters/{_slug(character.get('name'), f'Character-{character.get("id")}')}.md",
            'content': _character_markdown(character, payload['relations']),
        }
        for character in payload['characters']
    )
    files.extend(
        {
            'path': f"Foreshadows/{_slug(foreshadow.get('title'), f'Foreshadow-{foreshadow.get("id")}')}.md",
            'content': _foreshadow_markdown(foreshadow),
        }
        for foreshadow in payload['foreshadows']
    )
    files.extend(
        {
            'path': f"Chapters/Chapter-{chapter['id']}.md",
            'content': _chapter_markdown(chapter),
        }
        for chapter in payload['approved_chapters']
    )
    files.append({'path': 'Timeline/Events.md', 'content': _events_markdown(payload['events'])})
    return files


def export_world_markdown(db: Session, user: User, world_id: int) -> dict[str, Any]:
    world = require_owned_world(db, user, world_id)
    payload = build_world_archive_payload(db, world)
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'generated_at': datetime.now(timezone.utc),
        'files': render_markdown_bundle(payload),
    }
