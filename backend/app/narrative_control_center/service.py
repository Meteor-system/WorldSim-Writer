from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World
from app.world.service import count_approved_chapters, require_owned_world


APPROVED_STATUS = 'approved'


def _approved_chapters_query(world_id: int):
    return (
        select(Chapter)
        .where(Chapter.world_id == world_id)
        .where(Chapter.status == APPROVED_STATUS)
        .where(Chapter.approved_version.is_not(None))
        .where(Chapter.approved_content.is_not(None))
        .order_by(Chapter.id)
    )


def _require_owned_chapter(db: Session, user: User, chapter_id: int) -> Chapter:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    world = db.get(World, chapter.world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return chapter


def _chapter_events(db: Session, chapter_id: int) -> list[EventLog]:
    return list(db.scalars(select(EventLog).where(EventLog.chapter_id == chapter_id).order_by(EventLog.id)))


def _event_counts(events: list[EventLog]) -> dict[str, int]:
    return {
        'event_count': len(events),
        'character_change_count': sum(1 for event in events if event.event_type == 'character_change'),
        'foreshadow_change_count': sum(1 for event in events if event.event_type == 'foreshadow_change'),
    }


def _approved_excerpt(content: str, limit: int = 180) -> str:
    normalized = ' '.join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f'{normalized[:limit].rstrip()}…'


def _event_payload(event: EventLog) -> dict:
    return event.payload or {}


def _event_to_dict(event: EventLog) -> dict:
    return {
        'id': event.id,
        'event_type': event.event_type,
        'source_type': event.source_type,
        'world_version_before': event.world_version_before,
        'world_version_after': event.world_version_after,
        'payload': _event_payload(event),
        'created_at': event.created_at.isoformat(),
    }


def _event_change(event: EventLog) -> dict:
    payload = _event_payload(event)
    return {
        'event_type': event.event_type,
        'object_type': payload.get('object_type'),
        'object_id': payload.get('object_id'),
        'before': payload.get('before'),
        'after': payload.get('after'),
        'payload': payload,
    }


def _world_version_before(events: list[EventLog], chapter: Chapter) -> int:
    if events:
        return min(event.world_version_before for event in events)
    return chapter.base_world_version


def _world_version_after(events: list[EventLog], chapter: Chapter) -> int:
    if events:
        return max(event.world_version_after for event in events)
    return chapter.base_world_version


def _latest_approved_chapter(db: Session, world_id: int) -> Chapter | None:
    return db.scalar(_approved_chapters_query(world_id).order_by(desc(Chapter.id)))


def _latest_draft(db: Session, chapter: Chapter) -> ChapterDraft | None:
    return db.scalar(
        select(ChapterDraft)
        .where(ChapterDraft.chapter_id == chapter.id)
        .where(ChapterDraft.draft_version == chapter.draft_version)
    )


def _select_progression_hint(chapter: Chapter | None) -> dict | None:
    if chapter is None:
        return None
    report = chapter.character_arc_report or {}
    hints = report.get('progression_hints') or []
    for hint in hints:
        if hint.get('priority') == 'high' and hint.get('can_seed_next_chapter_goal') is True:
            return hint
    return None


def _next_story_arc_chapter(world: World, next_chapter_number: int) -> dict | None:
    for index, item in enumerate(world.story_arc or [], start=1):
        if not isinstance(item, dict):
            continue
        item_number = item.get('chapter_number') or item.get('number') or item.get('chapter') or index
        try:
            if int(item_number) == next_chapter_number:
                return item
        except (TypeError, ValueError):
            continue
    return None


def _characters_by_id(characters: list[Character]) -> dict[int, Character]:
    return {character.id: character for character in characters}


def _foreshadows_by_id(foreshadows: list[Foreshadow]) -> dict[int, Foreshadow]:
    return {foreshadow.id: foreshadow for foreshadow in foreshadows}


def _recommended_pov(
    selected_hint: dict | None,
    story_arc_chapter: dict | None,
    characters: list[Character],
) -> tuple[int | None, str | None]:
    character_by_id = _characters_by_id(characters)
    related_character_ids = selected_hint.get('related_character_ids') if selected_hint else []
    if isinstance(related_character_ids, list) and len(related_character_ids) == 1:
        character = character_by_id.get(related_character_ids[0])
        if character is not None:
            return character.id, character.name

    pov_suggestion = (story_arc_chapter or {}).get('pov_suggestion')
    if isinstance(pov_suggestion, str) and pov_suggestion:
        for character in characters:
            if character.name == pov_suggestion or character.name in pov_suggestion:
                return character.id, character.name

    for character in characters:
        if character.role_type == 'protagonist':
            return character.id, character.name
    if characters:
        return characters[0].id, characters[0].name
    return None, None


def _priority_characters(characters: list[Character], selected_hint: dict | None, latest_chapter: Chapter | None) -> list[dict]:
    character_by_id = _characters_by_id(characters)
    priority: list[dict] = []
    seen: set[int] = set()

    def add(character_id: int, reason: str) -> None:
        character = character_by_id.get(character_id)
        if character is None or character.id in seen:
            return
        seen.add(character.id)
        priority.append(
            {
                'character_id': character.id,
                'name': character.name,
                'role_type': character.role_type,
                'status': character.status,
                'reason': reason,
            }
        )

    for character_id in (selected_hint or {}).get('related_character_ids') or []:
        add(character_id, '上一章 progression hint 建议让该角色推动下一章。')

    report = (latest_chapter.character_arc_report if latest_chapter else {}) or {}
    for arc in report.get('character_arcs') or []:
        if arc.get('continuity_risk') in {'high', 'medium'}:
            add(arc.get('character_id'), '上一章角色弧线存在连续性风险，需要优先处理。')

    for character in characters:
        if character.role_type in {'protagonist', 'major'} and character.current_goals:
            add(character.id, '该核心角色当前仍有 active goals。')

    return priority


def _priority_foreshadows(foreshadows: list[Foreshadow], selected_hint: dict | None) -> list[dict]:
    foreshadow_by_id = _foreshadows_by_id(foreshadows)
    priority: list[dict] = []
    seen: set[int] = set()

    def add(foreshadow: Foreshadow | None, reason: str) -> None:
        if foreshadow is None or foreshadow.id in seen:
            return
        seen.add(foreshadow.id)
        priority.append(
            {
                'foreshadow_id': foreshadow.id,
                'title': foreshadow.title,
                'status': foreshadow.status,
                'urgency_level': foreshadow.urgency_level,
                'reason': reason,
            }
        )

    for foreshadow_id in (selected_hint or {}).get('related_foreshadow_ids') or []:
        add(foreshadow_by_id.get(foreshadow_id), '该伏笔与上一章 progression hint 相关。')

    urgent = sorted(
        [foreshadow for foreshadow in foreshadows if foreshadow.status in {'planted', 'advanced'}],
        key=lambda item: (-item.urgency_level, item.id),
    )
    for foreshadow in urgent[:3]:
        add(foreshadow, '该伏笔仍处于可推进状态且紧迫度较高。')

    return priority


def _continuity_warnings(latest_chapter: Chapter | None, story_arc_chapter: dict | None, characters: list[Character]) -> list[dict]:
    warnings: list[dict] = []
    report = (latest_chapter.character_arc_report if latest_chapter else {}) or {}
    for arc in report.get('character_arcs') or []:
        risk = arc.get('continuity_risk')
        if risk in {'high', 'medium'}:
            warnings.append(
                {
                    'severity': risk,
                    'category': 'character_arc',
                    'message': arc.get('risk_reason') or f"{arc.get('name', '角色')} 的弧线需要在下一章保持连续。",
                    'related_character_ids': [arc.get('character_id')] if arc.get('character_id') is not None else [],
                    'related_foreshadow_ids': [],
                }
            )

    critic_report = (latest_chapter.critique_report if latest_chapter else {}) or {}
    for issue in critic_report.get('issues') or []:
        if issue.get('severity') == 'high':
            warnings.append(
                {
                    'severity': 'high',
                    'category': 'critic',
                    'message': issue.get('message') or '上一章 Critic Report 存在高风险问题。',
                    'related_character_ids': [],
                    'related_foreshadow_ids': [],
                }
            )

    if story_arc_chapter is None:
        warnings.append(
            {
                'severity': 'medium',
                'category': 'story_arc',
                'message': 'story arc 中缺少下一章摘要，建议手动确认主线推进方向。',
                'related_character_ids': [],
                'related_foreshadow_ids': [],
            }
        )
    if not characters:
        warnings.append(
            {
                'severity': 'high',
                'category': 'character',
                'message': '当前世界没有可用角色，无法推荐 POV。',
                'related_character_ids': [],
                'related_foreshadow_ids': [],
            }
        )
    return warnings


def _recent_events(db: Session, world_id: int) -> list[dict]:
    events = list(db.scalars(select(EventLog).where(EventLog.world_id == world_id).order_by(desc(EventLog.id)).limit(10)))
    return [
        {
            'id': event.id,
            'event_type': event.event_type,
            'world_version_before': event.world_version_before,
            'world_version_after': event.world_version_after,
            'payload': _event_payload(event),
            'created_at': event.created_at.isoformat(),
        }
        for event in events
    ]


def get_approved_chapter_history(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    chapters = list(db.scalars(_approved_chapters_query(world.id)))
    items = []
    for chapter in chapters:
        events = _chapter_events(db, chapter.id)
        counts = _event_counts(events)
        items.append(
            {
                'id': chapter.id,
                'title': chapter.title,
                'status': chapter.status,
                'approved_version': chapter.approved_version,
                'base_world_version': chapter.base_world_version,
                'world_version_after': _world_version_after(events, chapter),
                'approved_excerpt': _approved_excerpt(chapter.approved_content or ''),
                **counts,
            }
        )
    return {'world_id': world.id, 'chapters': items}


def get_approved_chapter_history_detail(db: Session, user: User, chapter_id: int) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    if chapter.status != APPROVED_STATUS or chapter.approved_version is None or chapter.approved_content is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='CHAPTER_NOT_APPROVED')

    events = _chapter_events(db, chapter.id)
    latest_draft = _latest_draft(db, chapter)
    character_changes = [_event_change(event) for event in events if event.event_type == 'character_change']
    foreshadow_changes = [_event_change(event) for event in events if event.event_type == 'foreshadow_change']
    return {
        'id': chapter.id,
        'world_id': chapter.world_id,
        'title': chapter.title,
        'status': chapter.status,
        'approved_version': chapter.approved_version,
        'base_world_version': chapter.base_world_version,
        'approved_content': chapter.approved_content,
        'world_version_before': _world_version_before(events, chapter),
        'world_version_after': _world_version_after(events, chapter),
        'events': [_event_to_dict(event) for event in events],
        'character_changes': character_changes,
        'foreshadow_changes': foreshadow_changes,
        'critic_summary': (chapter.critique_report or {}).get('summary'),
        'character_arc_summary': (chapter.character_arc_report or {}).get('summary'),
        'execution_context': latest_draft.execution_context if latest_draft and latest_draft.execution_context else chapter.execution_context,
    }


def get_next_chapter_prep(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    approved_count = count_approved_chapters(db, world.id)
    next_chapter_number = approved_count + 1
    latest_chapter = _latest_approved_chapter(db, world.id)
    selected_hint = _select_progression_hint(latest_chapter)
    story_arc_chapter = _next_story_arc_chapter(world, next_chapter_number)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(
        db.scalars(
            select(Foreshadow)
            .where(Foreshadow.world_id == world.id)
            .order_by(Foreshadow.urgency_level.desc(), Foreshadow.id)
        )
    )

    source_signals: list[str] = []
    if selected_hint is not None:
        suggested_goal = selected_hint['suggested_next_beat']
        source_signals.append('character_arc_progression_hint')
    elif story_arc_chapter is not None and story_arc_chapter.get('summary'):
        suggested_goal = story_arc_chapter['summary']
        source_signals.append('story_arc')
    else:
        urgent_foreshadow = next((foreshadow for foreshadow in foreshadows if foreshadow.status in {'planted', 'advanced'}), None)
        if urgent_foreshadow is not None:
            suggested_goal = f'推进伏笔《{urgent_foreshadow.title}》，让相关角色围绕该线索做出新的选择。'
            source_signals.append('urgent_foreshadow')
        else:
            suggested_goal = '基于最近世界事件继续推进主线冲突，并让核心角色做出新的选择。'
            source_signals.append('fallback')

    if story_arc_chapter is not None and 'story_arc' not in source_signals:
        source_signals.append('story_arc')

    recommended_pov_character_id, recommended_pov_character_name = _recommended_pov(selected_hint, story_arc_chapter, characters)
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'next_chapter_number': next_chapter_number,
        'suggested_goal': suggested_goal,
        'recommended_pov_character_id': recommended_pov_character_id,
        'recommended_pov_character_name': recommended_pov_character_name,
        'source_signals': source_signals,
        'priority_characters': _priority_characters(characters, selected_hint, latest_chapter),
        'priority_foreshadows': _priority_foreshadows(foreshadows, selected_hint),
        'progression_hints': (latest_chapter.character_arc_report or {}).get('progression_hints', []) if latest_chapter else [],
        'continuity_warnings': _continuity_warnings(latest_chapter, story_arc_chapter, characters),
        'recent_events': _recent_events(db, world.id),
    }
