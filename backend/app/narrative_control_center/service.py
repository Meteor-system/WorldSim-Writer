from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.foreshadow.service import build_foreshadow_ledger
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


def _priority_foreshadows(foreshadows: list[Foreshadow], selected_hint: dict | None, ledger_high_pressure: list[dict] | None = None) -> list[dict]:
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

    for entry in ledger_high_pressure or []:
        foreshadow = entry['foreshadow']
        reasons = entry.get('pressure_reasons') or []
        reason = '；'.join(reasons) if reasons else '该伏笔仍处于可推进状态且紧迫度较高。'
        add(foreshadow, reason)

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


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _health_metric(key: str, label: str, value: int | float, metric_status: str, detail: str) -> dict:
    return {'key': key, 'label': label, 'value': value, 'status': metric_status, 'detail': detail}


def _health_risk(severity: str, source: str, message: str, suggested_action: str, object_type=None, object_id=None, object_title=None) -> dict:
    return {
        'severity': severity,
        'source': source,
        'message': message,
        'object_type': object_type,
        'object_id': object_id,
        'object_title': object_title,
        'suggested_action': suggested_action,
    }


def _critic_reports(chapters: list[Chapter]) -> list[dict]:
    return [chapter.critique_report for chapter in chapters if chapter.critique_report]


def _average_score(reports: list[dict]) -> int | None:
    scores = [int(report.get('overall_score')) for report in reports if report.get('overall_score') is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores))


def get_narrative_health(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    approved_chapters = list(db.scalars(_approved_chapters_query(world.id)))
    latest_chapter = approved_chapters[-1] if approved_chapters else None
    critic_reports = _critic_reports(approved_chapters)
    average_critic_score = _average_score(critic_reports)
    ledger = build_foreshadow_ledger(db, world)
    recent_event_count = db.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world.id)) or 0

    risks: list[dict] = []
    high_critic_count = 0
    medium_critic_count = 0
    for chapter in approved_chapters:
        for issue in (chapter.critique_report or {}).get('issues', []):
            severity = issue.get('severity')
            if severity == 'high':
                high_critic_count += 1
                risks.append(_health_risk('high', 'critic', issue.get('message') or 'Critic 高风险问题。', '修订最近章节或重新生成 Critic 报告。', 'chapter', chapter.id, chapter.title))
            elif severity == 'medium':
                medium_critic_count += 1
                risks.append(_health_risk('medium', 'critic', issue.get('message') or 'Critic 中风险问题。', '复核对应章节的节奏、对白或结构。', 'chapter', chapter.id, chapter.title))

    high_arc_count = 0
    medium_arc_count = 0
    for chapter in approved_chapters:
        report = chapter.character_arc_report or {}
        for arc in report.get('character_arcs', []):
            risk = arc.get('continuity_risk')
            if risk == 'high':
                high_arc_count += 1
                risks.append(_health_risk('high', 'character_arc', arc.get('risk_reason') or '角色弧线存在高风险。', '在下一章补足角色选择与转折铺垫。', 'character', arc.get('character_id'), arc.get('name')))
            elif risk == 'medium':
                medium_arc_count += 1
                risks.append(_health_risk('medium', 'character_arc', arc.get('risk_reason') or '角色弧线存在中风险。', '复核角色弧线连续性。', 'character', arc.get('character_id'), arc.get('name')))
        for note in report.get('relationship_notes', []):
            risk = note.get('risk_level')
            title = f"{note.get('source_name', '角色')} → {note.get('target_name', '角色')}"
            if risk == 'high':
                high_arc_count += 1
                risks.append(_health_risk('high', 'character_arc', note.get('risk_reason') or '关系推进存在高风险。', '补足关系变化的场景因果。', 'relationship', None, title))
            elif risk == 'medium':
                medium_arc_count += 1
                risks.append(_health_risk('medium', 'character_arc', note.get('risk_reason') or '关系推进存在中风险。', '复核关系变化承接。', 'relationship', None, title))

    high_pressure_entries = ledger['high_pressure']
    for entry in high_pressure_entries:
        foreshadow = entry['foreshadow']
        risks.append(_health_risk('medium', 'foreshadow', '；'.join(entry.get('pressure_reasons') or []) or '高压伏笔需要推进。', '优先在下一章推进或回收该伏笔。', 'foreshadow', foreshadow.id, foreshadow.title))

    score = 100
    score -= high_critic_count * 12
    score -= medium_critic_count * 6
    score -= high_arc_count * 12
    score -= medium_arc_count * 6
    score -= len(high_pressure_entries) * 5
    if not approved_chapters:
        score -= 5
    health_score = _clamp_score(score)
    has_high_risk = any(risk['severity'] == 'high' for risk in risks)
    has_medium_risk = any(risk['severity'] == 'medium' for risk in risks)
    if health_score < 60 or has_high_risk:
        health_status = 'at_risk'
    elif health_score < 80 or has_medium_risk:
        health_status = 'watch'
    else:
        health_status = 'healthy'

    metrics = [
        _health_metric('approved_chapters', '已批准章节', len(approved_chapters), 'ok' if approved_chapters else 'watch', '已正式写入世界历史的章节数量。'),
        _health_metric('average_critic_score', '平均 Critic 分', average_critic_score or 0, 'ok' if average_critic_score is None or average_critic_score >= 75 else 'watch', '来自已存储 Critic 报告的平均分。'),
        _health_metric('critic_issues', 'Critic 风险', high_critic_count + medium_critic_count, 'risk' if high_critic_count else 'watch' if medium_critic_count else 'ok', f'高风险 {high_critic_count}，中风险 {medium_critic_count}。'),
        _health_metric('character_arc_risks', '角色弧线风险', high_arc_count + medium_arc_count, 'risk' if high_arc_count else 'watch' if medium_arc_count else 'ok', f'高风险 {high_arc_count}，中风险 {medium_arc_count}。'),
        _health_metric('open_foreshadows', '开放伏笔', ledger['summary']['open_count'], 'watch' if ledger['summary']['open_count'] else 'ok', '仍未 resolved/expired 的伏笔数量。'),
        _health_metric('high_pressure_foreshadows', '高压伏笔', len(high_pressure_entries), 'watch' if high_pressure_entries else 'ok', '来自 Foreshadow Ledger 的高压伏笔。'),
        _health_metric('recent_events', '正式事件', recent_event_count, 'ok', '当前世界累计正式事件数量。'),
    ]

    actions = []
    if not approved_chapters:
        actions.append({'action_key': 'write_first_chapter', 'label': '生成第一章', 'detail': '当前世界尚无已批准章节，先完成首章闭环。'})
    if has_high_risk:
        actions.append({'action_key': 'revise_latest_chapter', 'label': '优先修订最近章节', 'detail': '存在高风险 Critic 或角色弧线问题，建议修订后再继续。'})
    if high_pressure_entries:
        actions.append({'action_key': 'advance_foreshadow', 'label': '推进高压伏笔', 'detail': '下一章目标应优先处理高压伏笔。'})
    if latest_chapter and not actions:
        actions.append({'action_key': 'continue_next_chapter', 'label': '继续下一章', 'detail': '当前没有高风险阻塞，可以进入下一章准备台。'})

    risks.sort(key=lambda item: {'high': 0, 'medium': 1, 'low': 2}.get(item['severity'], 3))
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'health_score': health_score,
        'status': health_status,
        'summary': {
            'approved_chapter_count': len(approved_chapters),
            'latest_chapter_id': latest_chapter.id if latest_chapter else None,
            'latest_chapter_title': latest_chapter.title if latest_chapter else None,
            'average_critic_score': average_critic_score,
            'high_risk_count': sum(1 for risk in risks if risk['severity'] == 'high'),
            'medium_risk_count': sum(1 for risk in risks if risk['severity'] == 'medium'),
            'open_foreshadow_count': ledger['summary']['open_count'],
            'high_pressure_foreshadow_count': len(high_pressure_entries),
        },
        'metrics': metrics,
        'risks': risks[:10],
        'suggested_actions': actions,
    }


PRIORITY_RANK = {'must_close': 0, 'should_advance': 1, 'can_delay': 2, 'can_leave_open': 3}
THREAD_PRESSURE_RANK = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}


def _open_thread(
    thread_id: str,
    thread_type: str,
    priority: str,
    pressure_level: str,
    title: str,
    summary: str,
    suggested_action: str,
    related_object_type: str | None = None,
    related_object_id: int | None = None,
    related_character_ids: list[int] | None = None,
    related_foreshadow_ids: list[int] | None = None,
    can_seed_next_chapter_goal: bool = False,
) -> dict:
    return {
        'thread_id': thread_id,
        'thread_type': thread_type,
        'priority': priority,
        'pressure_level': pressure_level,
        'title': title,
        'summary': summary,
        'related_object_type': related_object_type,
        'related_object_id': related_object_id,
        'related_character_ids': related_character_ids or [],
        'related_foreshadow_ids': related_foreshadow_ids or [],
        'suggested_action': suggested_action,
        'can_seed_next_chapter_goal': can_seed_next_chapter_goal,
    }


def _thread_priority_counts(threads: list[dict]) -> dict[str, int]:
    return {
        'must_close_count': sum(1 for thread in threads if thread['priority'] == 'must_close'),
        'should_advance_count': sum(1 for thread in threads if thread['priority'] == 'should_advance'),
        'can_delay_count': sum(1 for thread in threads if thread['priority'] == 'can_delay'),
        'can_leave_open_count': sum(1 for thread in threads if thread['priority'] == 'can_leave_open'),
    }


def _narrative_entropy(total_open_threads: int, must_close_count: int) -> str:
    if must_close_count >= 2 or total_open_threads >= 10:
        return 'high'
    if must_close_count >= 1 or total_open_threads >= 5:
        return 'medium'
    return 'low'


def _foreshadow_thread(entry: dict) -> dict:
    foreshadow = entry['foreshadow']
    pressure_level = entry['pressure_level']
    if pressure_level == 'critical' or entry.get('is_overdue'):
        priority = 'must_close'
        action = '下一章优先回收或明确处理该伏笔，避免叙事债务继续累积。'
    elif pressure_level == 'high':
        priority = 'should_advance'
        action = '下一章推进该伏笔，给出新信息、反转或阶段性兑现。'
    else:
        priority = 'can_delay'
        action = '保持记录，可在后续章节继续铺垫或合并到更高压线索。'
    reasons = entry.get('pressure_reasons') or []
    summary = '；'.join(reasons) if reasons else foreshadow.description
    return _open_thread(
        thread_id=f'foreshadow:{foreshadow.id}',
        thread_type='foreshadow',
        priority=priority,
        pressure_level=pressure_level,
        title=foreshadow.title,
        summary=summary,
        related_object_type='foreshadow',
        related_object_id=foreshadow.id,
        related_character_ids=list(foreshadow.related_character_ids or []),
        related_foreshadow_ids=[foreshadow.id],
        suggested_action=action,
        can_seed_next_chapter_goal=priority in {'must_close', 'should_advance'},
    )


def _character_goal_threads(characters: list[Character]) -> list[dict]:
    threads: list[dict] = []
    for character in characters:
        for index, goal in enumerate(character.current_goals or []):
            is_core = character.role_type in {'protagonist', 'major'}
            threads.append(
                _open_thread(
                    thread_id=f'character_goal:{character.id}:{index}',
                    thread_type='character_goal',
                    priority='should_advance' if is_core else 'can_delay',
                    pressure_level='medium' if is_core else 'low',
                    title=f'{character.name}：{goal}',
                    summary=f'{character.name} 当前仍有 active goal：{goal}',
                    related_object_type='character',
                    related_object_id=character.id,
                    related_character_ids=[character.id],
                    suggested_action='在下一章给该目标一次选择、阻力或阶段性结果。' if is_core else '可延后处理，或合并到主线/伏笔推进中。',
                    can_seed_next_chapter_goal=is_core,
                )
            )
    return threads


def _progression_hint_threads(latest_chapter: Chapter | None) -> list[dict]:
    if latest_chapter is None:
        return []
    hints = ((latest_chapter.character_arc_report or {}).get('progression_hints') or [])
    threads: list[dict] = []
    for index, hint in enumerate(hints):
        priority = 'should_advance' if hint.get('priority') == 'high' else 'can_delay'
        threads.append(
            _open_thread(
                thread_id=f'progression_hint:{index}',
                thread_type='progression_hint',
                priority=priority,
                pressure_level='medium' if priority == 'should_advance' else 'low',
                title=hint.get('title') or '上一章推进提示',
                summary=hint.get('rationale') or hint.get('suggested_next_beat') or '上一章报告建议继续推进该线索。',
                related_character_ids=hint.get('related_character_ids') or [],
                related_foreshadow_ids=hint.get('related_foreshadow_ids') or [],
                suggested_action=hint.get('suggested_next_beat') or '将该提示转化为下一章目标。',
                can_seed_next_chapter_goal=bool(hint.get('can_seed_next_chapter_goal')),
            )
        )
    return threads


def _health_risk_threads(health: dict) -> list[dict]:
    threads: list[dict] = []
    for index, risk in enumerate(health.get('risks') or []):
        severity = risk.get('severity')
        priority = 'must_close' if severity == 'high' else 'should_advance'
        threads.append(
            _open_thread(
                thread_id=f"health_risk:{risk.get('source', 'risk')}:{index}",
                thread_type='health_risk',
                priority=priority,
                pressure_level='high' if severity == 'high' else 'medium',
                title=risk.get('object_title') or risk.get('source') or '叙事风险',
                summary=risk.get('message') or 'Narrative Health 检测到需要处理的风险。',
                related_object_type=risk.get('object_type'),
                related_object_id=risk.get('object_id'),
                suggested_action=risk.get('suggested_action') or '优先复核该风险。',
                can_seed_next_chapter_goal=priority == 'must_close',
            )
        )
    return threads


def get_open_threads(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    ledger = build_foreshadow_ledger(db, world)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    latest_chapter = _latest_approved_chapter(db, world.id)
    health = get_narrative_health(db, user, world.id)

    threads: list[dict] = []
    ledger_entries = [entry for group in ledger['groups'].values() for entry in group]
    threads.extend(_foreshadow_thread(entry) for entry in ledger_entries if entry['is_open'])
    threads.extend(_character_goal_threads(characters))
    threads.extend(_progression_hint_threads(latest_chapter))
    threads.extend(_health_risk_threads(health))

    seen: set[str] = set()
    deduped_threads: list[dict] = []
    for thread in threads:
        if thread['thread_id'] in seen:
            continue
        seen.add(thread['thread_id'])
        deduped_threads.append(thread)
    deduped_threads.sort(
        key=lambda thread: (
            PRIORITY_RANK.get(thread['priority'], 9),
            THREAD_PRESSURE_RANK.get(thread['pressure_level'], 9),
            thread['thread_id'],
        )
    )

    counts = _thread_priority_counts(deduped_threads)
    total_foreshadows = ledger['summary']['total']
    closed_foreshadows = ledger['summary']['resolved_count'] + ledger['summary']['expired_count']
    convergence_ratio = round(closed_foreshadows / max(total_foreshadows, 1), 2)
    recent_event_count = db.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world.id)) or 0
    suggested_next_actions = []
    seed_thread = next((thread for thread in deduped_threads if thread['can_seed_next_chapter_goal']), None)
    if seed_thread is not None:
        suggested_next_actions.append(
            {
                'action_key': 'seed_next_chapter_goal',
                'label': '用最高压开放线索规划下一章',
                'detail': seed_thread['suggested_action'],
                'thread_id': seed_thread['thread_id'],
            }
        )
    if counts['must_close_count']:
        suggested_next_actions.append(
            {
                'action_key': 'reduce_entropy',
                'label': '先收束再扩张',
                'detail': '当前存在 must_close 线索，建议下一章减少新增设定，优先兑现旧承诺。',
            }
        )

    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'summary': {
            'total_open_threads': len(deduped_threads),
            **counts,
            'convergence_ratio': convergence_ratio,
            'narrative_entropy_level': _narrative_entropy(len(deduped_threads), counts['must_close_count']),
            'recent_event_count': recent_event_count,
        },
        'threads': deduped_threads[:20],
        'suggested_next_actions': suggested_next_actions,
    }



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

    ledger = build_foreshadow_ledger(db, world)
    high_pressure_foreshadows = ledger['high_pressure']

    source_signals: list[str] = []
    if selected_hint is not None:
        suggested_goal = selected_hint['suggested_next_beat']
        source_signals.append('character_arc_progression_hint')
    elif story_arc_chapter is not None and story_arc_chapter.get('summary'):
        suggested_goal = story_arc_chapter['summary']
        source_signals.append('story_arc')
    else:
        urgent_entry = next(iter(high_pressure_foreshadows), None)
        urgent_foreshadow = urgent_entry['foreshadow'] if urgent_entry is not None else next((foreshadow for foreshadow in foreshadows if foreshadow.status in {'planted', 'advanced'}), None)
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
        'priority_foreshadows': _priority_foreshadows(foreshadows, selected_hint, high_pressure_foreshadows),
        'progression_hints': (latest_chapter.character_arc_report or {}).get('progression_hints', []) if latest_chapter else [],
        'continuity_warnings': _continuity_warnings(latest_chapter, story_arc_chapter, characters),
        'recent_events': _recent_events(db, world.id),
    }
