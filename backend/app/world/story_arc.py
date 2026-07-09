from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.core.config import get_settings
from app.foreshadow.models import Foreshadow
from app.foreshadow.service import build_foreshadow_ledger
from app.llm.client import LLMClient
from app.llm.schemas import StoryArcChapter
from app.world.governance import require_owned_world_for_update
from app.world.models import World
from app.world.service import count_approved_chapters, require_owned_world


def _model_client(llm_client: LLMClient | None = None) -> LLMClient:
    settings = get_settings()
    client = llm_client or LLMClient()
    if hasattr(client, 'mock'):
        client.mock = settings.llm_mock
    return client


SAFE_MODEL_RUNTIME_ERRORS = {'MODEL_REQUEST_FAILED', 'MODEL_AUTH_FAILED', 'MODEL_RATE_LIMITED'}


def _map_model_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='MODEL_TIMEOUT')
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
    if isinstance(exc, RuntimeError) and str(exc) in SAFE_MODEL_RUNTIME_ERRORS:
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_REQUEST_FAILED')


def _load_story_arc_context(db: Session, world: World) -> tuple[list[Character], list[Foreshadow]]:
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(
        db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.urgency_level.desc(), Foreshadow.id))
    )
    return characters, foreshadows


def build_story_arc_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    approved_chapter_count: int,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(
        f'- {character.id}: {character.name}, role={character.role_type}, status={character.status}, goals={character.current_goals}, profile={character.public_profile}'
        for character in characters
    )
    foreshadow_lines = '\n'.join(
        f'- {foreshadow.id}: {foreshadow.title}, type={foreshadow.foreshadow_type}, status={foreshadow.status}, urgency={foreshadow.urgency_level}, window={foreshadow.expected_resolution_window}, description={foreshadow.description}'
        for foreshadow in foreshadows
    )
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 Story Arc Planner。必须只返回严格 JSON 数组，不要返回对象包装、Markdown、解释或代码块。'
                '数组必须正好 10 章，每章对象只能包含字段：'
                'chapter_number, title, summary, core_conflict, pov_suggestion, foreshadow_hints。'
                'chapter_number 必须从 1 到 10 顺序排列。summary 必须是 1-2 句。'
                'foreshadow_hints 必须使用输入伏笔的 title 或 type 作为 tag，可以为空数组。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界标题：{world.title}\n'
                f'类型模板：{world.genre_template}\n'
                f'语气配置：{world.tone_profile}\n'
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'已批准章节数：{approved_chapter_count}\n'
                f'角色：\n{character_lines or "无"}\n'
                f'伏笔：\n{foreshadow_lines or "无"}\n'
                '请规划前 10 章故事弧线，保持冲突递进、角色目标变化和伏笔推进节奏。'
            ),
        },
    ]


def build_suggest_goal_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    approved_chapter_count: int,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(
        f'- {character.name}（{character.role_type}）: 当前状态={character.status}, 目标={character.current_goals}'
        for character in characters
    )
    foreshadow_lines = '\n'.join(
        f'- {foreshadow.title}（{foreshadow.foreshadow_type}）: 状态={foreshadow.status}, 紧迫度={foreshadow.urgency_level}, 描述={foreshadow.description}'
        for foreshadow in foreshadows
    )
    next_chapter = approved_chapter_count + 1
    story_arc_hint = ''
    if world.story_arc:
        for arc_ch in world.story_arc:
            if isinstance(arc_ch, dict) and arc_ch.get('chapter_number') == next_chapter:
                story_arc_hint = (
                    f"\n故事大纲参考（第{next_chapter}章）：\n"
                    f"标题：{arc_ch.get('title', '未知')}\n"
                    f"概要：{arc_ch.get('summary', '未知')}\n"
                    f"核心冲突：{arc_ch.get('core_conflict', '未知')}\n"
                    f"建议POV：{arc_ch.get('pov_suggestion', '未知')}"
                )
                break
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的章节目标生成器。你的任务是为一个完全不会写小说的用户生成一章的"章节目标"。'
                '章节目标应该用 2-3 句自然语言描述这一章要讲什么故事、推进什么冲突、展示什么角色变化。'
                '语言要生动具体，让新手一看就知道该怎么写。不要用元术语（如"推进伏笔"），而是用故事化的语言描述。'
                '必须只返回 JSON 对象：{"goal": "章节目标文本"}。不要返回其他内容。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界标题：{world.title}\n'
                f'类型：{world.genre_template}\n'
                f'世界设定：{world.truth_canon}\n'
                f'已写完章节数：{approved_chapter_count}\n'
                f'角色：\n{character_lines or "暂无角色"}\n'
                f'伏笔：\n{foreshadow_lines or "暂无伏笔"}'
                f'{story_arc_hint}\n'
                f'请为第 {next_chapter} 章生成一个章节目标。'
            ),
        },
    ]


def suggest_chapter_goal(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
    characters, foreshadows = _load_story_arc_context(db, world)
    approved_count = count_approved_chapters(db, world.id)
    client = _model_client(llm_client)
    try:
        result = client.suggest_goal(build_suggest_goal_messages(world, characters, foreshadows, approved_count))
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    return result


def generate_story_arc(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world_for_update(db, user, world_id)
    characters, foreshadows = _load_story_arc_context(db, world)
    approved_count = count_approved_chapters(db, world.id)
    client = _model_client(llm_client)
    try:
        chapters = client.generate_story_arc(build_story_arc_messages(world, characters, foreshadows, approved_count))
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc

    world.story_arc = [chapter.model_dump() if isinstance(chapter, StoryArcChapter) else chapter for chapter in chapters]
    db.commit()
    db.refresh(world)
    return {'world_id': world.id, 'story_arc': world.story_arc}


def _serial_goal_from_arc_chapter(chapter: dict) -> str:
    title = chapter.get('title') or f"第 {chapter.get('chapter_number', '?')} 章"
    summary = chapter.get('summary') or ''
    conflict = chapter.get('core_conflict') or ''
    pov = chapter.get('pov_suggestion') or '未指定'
    parts = [f'{title}：{summary}']
    if conflict:
        parts.append(f'核心冲突：{conflict}')
    parts.append(f'建议 POV：{pov}')
    return ' '.join(parts)


def _serial_convergence_guidance(db: Session, world: World) -> dict:
    ledger = build_foreshadow_ledger(db, world)
    summary = ledger['summary']
    high_pressure_entries = ledger['high_pressure']
    priority_foreshadows = [
        {
            'foreshadow_id': entry['foreshadow'].id,
            'title': entry['foreshadow'].title,
            'status': entry['foreshadow'].status,
            'urgency_level': entry['foreshadow'].urgency_level,
            'pressure_level': entry['pressure_level'],
            'pressure_reasons': entry['pressure_reasons'],
        }
        for entry in high_pressure_entries[:3]
    ]
    if summary['overdue_count']:
        mode = 'converge'
        mode_label = '叙事收束'
        recommendation = '存在逾期伏笔；后续队列应优先回收旧承诺，暂停扩张新线索。'
    elif summary['high_urgency_count'] or summary['stale_count']:
        mode = 'pressure'
        mode_label = '继续加压'
        recommendation = '存在高压或久未推进伏笔；后续章节应至少推进一个既有悬念/伏笔。'
    elif summary['open_count']:
        mode = 'balanced'
        mode_label = '平衡推进'
        recommendation = '已有开放悬念/伏笔；连载队列可以推进主线，但避免只铺设新线索。'
    else:
        mode = 'expand'
        mode_label = '可适度扩张'
        recommendation = '当前没有开放悬念/伏笔；可以为下一轮故事埋设少量可追踪线索。'
    return {
        'mode': mode,
        'mode_label': mode_label,
        'open_foreshadow_count': summary['open_count'],
        'high_pressure_count': len(high_pressure_entries),
        'stale_count': summary['stale_count'],
        'overdue_count': summary['overdue_count'],
        'priority_foreshadows': priority_foreshadows,
        'recommendation': recommendation,
        'guidance_notes': [
            '收束提示来自现有悬念/伏笔账本，只用于规划目标队列。',
            '这些提示不会写入正史、不会关闭伏笔，也不会推进世界进度。',
        ],
    }


def preview_serial_plan(db: Session, user: User, world_id: int, limit: int = 3) -> dict:
    world = require_owned_world(db, user, world_id)
    approved_count = count_approved_chapters(db, world.id)
    next_chapter_number = approved_count + 1
    queue = []
    for chapter in world.story_arc or []:
        if not isinstance(chapter, dict):
            continue
        chapter_number = chapter.get('chapter_number')
        if not isinstance(chapter_number, int) or chapter_number < next_chapter_number:
            continue
        queue.append(
            {
                'chapter_number': chapter_number,
                'title': chapter.get('title') or f'第 {chapter_number} 章',
                'goal': _serial_goal_from_arc_chapter(chapter),
                'summary': chapter.get('summary') or '',
                'core_conflict': chapter.get('core_conflict') or '',
                'pov_suggestion': chapter.get('pov_suggestion') or '',
                'foreshadow_hints': chapter.get('foreshadow_hints') or [],
                'source': 'story_arc',
            }
        )
        if len(queue) >= limit:
            break
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'approved_chapter_count': approved_count,
        'queue': queue,
        'safety_notes': [
            '这是多章目标队列预览，不会一次性生成正文。',
            '每章仍需单独进入 Studio 创建草稿、审稿并由用户确认。',
            '世界进度和 EventLog 只会在章节写入正史后更新。',
        ],
        'convergence_guidance': _serial_convergence_guidance(db, world),
    }
