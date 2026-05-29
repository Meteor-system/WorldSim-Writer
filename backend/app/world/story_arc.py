from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.core.config import get_settings
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import StoryArcChapter
from app.world.models import World
from app.world.service import count_approved_chapters, require_owned_world


def _model_client(llm_client: LLMClient | None = None) -> LLMClient:
    settings = get_settings()
    client = llm_client or LLMClient()
    if hasattr(client, 'mock'):
        client.mock = settings.llm_mock
    return client


def _map_model_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='MODEL_TIMEOUT')
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
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


def generate_story_arc(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
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
