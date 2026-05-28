from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import ChapterGeneration
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World
from app.world.service import require_owned_world


def build_generation_messages(
    world,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    chapter_goal: str,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}' for f in foreshadows)
    return [
        {'role': 'system', 'content': '你是长篇小说创作系统的章节起草助手。必须只返回 JSON。'},
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'角色：\n{character_lines}\n'
                f'伏笔：\n{foreshadow_lines}\n'
                f'本章目标：{chapter_goal}\n'
                '返回字段：title, draft_content, context_summary, review_hints, '
                'proposed_character_changes, proposed_foreshadow_changes。'
            ),
        },
    ]


def validate_generation_ids(generation: ChapterGeneration, characters: list[Character], foreshadows: list[Foreshadow]) -> None:
    character_ids = {character.id for character in characters}
    foreshadow_ids = {foreshadow.id for foreshadow in foreshadows}
    if any(change.character_id not in character_ids for change in generation.proposed_character_changes):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
    if any(change.foreshadow_id not in foreshadow_ids for change in generation.proposed_foreshadow_changes):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')


def create_chapter_draft(
    db: Session,
    user: User,
    world_id: int,
    chapter_goal: str,
    llm_client: LLMClient | None = None,
) -> dict:
    world = require_owned_world(db, user, world_id)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(
        db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.urgency_level.desc(), Foreshadow.id))
    )
    client = llm_client or LLMClient()
    try:
        generation = client.generate_chapter(build_generation_messages(world, characters, foreshadows, chapter_goal))
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='MODEL_TIMEOUT') from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID') from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_REQUEST_FAILED') from exc
    validate_generation_ids(generation, characters, foreshadows)

    chapter = Chapter(
        world_id=world.id,
        title=generation.title,
        pov_character_id=characters[0].id if characters else None,
        status='reviewing',
        draft_version=1,
        base_world_version=world.world_version,
    )
    db.add(chapter)
    db.flush()
    proposed_changes = {
        'characters': [change.model_dump(exclude_none=True) for change in generation.proposed_character_changes],
        'foreshadows': [change.model_dump(exclude_none=True) for change in generation.proposed_foreshadow_changes],
    }
    draft = ChapterDraft(
        chapter_id=chapter.id,
        draft_version=1,
        content=generation.draft_content,
        context_summary=generation.context_summary,
        review_hints=generation.review_hints,
        proposed_changes=proposed_changes,
        source_world_version=world.world_version,
    )
    db.add(draft)
    db.commit()
    db.refresh(chapter)
    db.refresh(draft)
    return {
        'chapter_id': chapter.id,
        'draft_id': draft.id,
        'title': chapter.title,
        'content': draft.content,
        'context_summary': draft.context_summary,
        'review_hints': draft.review_hints,
        'proposed_changes': draft.proposed_changes,
        'source_world_version': draft.source_world_version,
    }


def approve_chapter(db: Session, user: User, chapter_id: int) -> Chapter:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    world = db.scalar(select(World).where(World.id == chapter.world_id).with_for_update())
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    draft = db.scalar(
        select(ChapterDraft)
        .where(ChapterDraft.chapter_id == chapter.id)
        .where(ChapterDraft.draft_version == chapter.draft_version)
    )
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if draft.source_world_version != world.world_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_VERSION_MISMATCH')

    version_before = world.world_version
    chapter.status = 'approved'
    chapter.approved_content = draft.content
    chapter.approved_version = draft.draft_version

    for change in draft.proposed_changes.get('characters', []):
        character = db.get(Character, change['character_id'])
        if character is None or character.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        if 'status' in change:
            character.status = change['status']
        if 'current_goals' in change:
            character.current_goals = change['current_goals']

    for change in draft.proposed_changes.get('foreshadows', []):
        foreshadow = db.get(Foreshadow, change['foreshadow_id'])
        if foreshadow is None or foreshadow.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        foreshadow.status = change['status']
        if change.get('description_note'):
            foreshadow.description = f"{foreshadow.description}\n审核备注：{change['description_note']}"

    world.world_version = version_before + 1
    db.add(
        EventLog(
            world_id=world.id,
            event_type='CHAPTER_APPROVED',
            source_type='chapter',
            commit_id=f'chapter-{chapter.id}-{uuid4().hex}',
            payload={
                'chapter_id': chapter.id,
                'chapter_title': chapter.title,
                'proposed_changes': draft.proposed_changes,
            },
            world_version_before=version_before,
            world_version_after=world.world_version,
        )
    )
    db.commit()
    db.refresh(chapter)
    return chapter
