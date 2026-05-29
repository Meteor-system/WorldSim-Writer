from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.core.config import get_settings
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.foreshadow.service import apply_foreshadow_status_transition
from app.llm.client import LLMClient
from app.llm.schemas import BeatCard, ChapterGeneration
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World
from app.world.service import character_projection, foreshadow_projection, refresh_world_projection, require_owned_world


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


def _require_owned_chapter(db: Session, user: User, chapter_id: int) -> Chapter:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    world = db.scalar(select(World).where(World.id == chapter.world_id))
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return chapter


def _latest_draft(db: Session, chapter: Chapter) -> ChapterDraft | None:
    return db.scalar(
        select(ChapterDraft)
        .where(ChapterDraft.chapter_id == chapter.id)
        .where(ChapterDraft.draft_version == chapter.draft_version)
    )


def _load_world_context(db: Session, world: World) -> tuple[list[Character], list[Foreshadow]]:
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(
        db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.urgency_level.desc(), Foreshadow.id))
    )
    return characters, foreshadows


def _outline_context_payload(outline) -> dict:
    return {
        'core_conflict': outline.core_conflict,
        'pov_suggestion': outline.pov_suggestion,
        'pacing': outline.pacing,
        'role_skill_targets': outline.role_skill_targets,
    }


def _draft_payload(chapter: Chapter, draft: ChapterDraft) -> dict:
    return {
        'chapter_id': chapter.id,
        'draft_id': draft.id,
        'title': chapter.title,
        'content': draft.content,
        'context_summary': draft.context_summary,
        'review_hints': draft.review_hints,
        'proposed_changes': draft.proposed_changes,
        'source_world_version': draft.source_world_version,
        'status': chapter.status,
        'approved_content': chapter.approved_content,
        'rejection_feedback': draft.rejection_feedback,
        'outline_beats': chapter.outline_beats,
        'outline_context': chapter.outline_context,
        'critique_report': chapter.critique_report,
    }


def build_outline_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    chapter_goal: str,
    chapter_context: str | None = None,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}' for f in foreshadows[:3])
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 Outliner Agent。必须只返回合法 JSON，结构为：'
                '{"core_conflict":"本章核心冲突","pov_suggestion":"建议POV",'
                '"pacing":"节奏倾向","role_skill_targets":["角色名"],'
                '"beats":[{"beat_id":"beat-1","summary":"节拍摘要","pov_character":"角色名",'
                '"location":"地点","emotional_arc":"情绪弧线","key_dialogue_hints":["对白提示"]}]}。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'角色：\n{character_lines}\n'
                f'紧迫伏笔：\n{foreshadow_lines}\n'
                f'本章目标：{chapter_goal}\n'
                f'用户额外上下文：{chapter_context or "无"}\n'
                '请输出 beat cards，不要写正文。'
            ),
        },
    ]


def build_generation_messages(
    world,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    chapter_goal: str,
    outline_beats: list[dict] | None = None,
    outline_context: dict | None = None,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}' for f in foreshadows)
    outline_lines = ''
    if outline_context:
        outline_lines += f'Outliner上下文：{outline_context}\n'
    if outline_beats:
        outline_lines += 'Outliner节拍：\n' + '\n'.join(
            f"- {beat.get('beat_id')}: {beat.get('summary')} | POV={beat.get('pov_character')} | location={beat.get('location')} | arc={beat.get('emotional_arc')} | dialogue={beat.get('key_dialogue_hints')}"
            for beat in outline_beats
        )
    return [
        {'role': 'system', 'content': '你是长篇小说创作系统的 Writer Agent。必须只返回合法的 JSON，字段结构如下：\n'
         '{"title": "章节标题", "draft_content": "正文内容", "context_summary": "摘要", '
         '"review_hints": ["提示1", "提示2"], '
         '"proposed_character_changes": [{"character_id": 整数, "status": "新状态", "current_goals": ["目标1"]}], '
         '"proposed_foreshadow_changes": [{"foreshadow_id": 整数, "status": "advanced|resolved|expired", "description_note": "备注"}]}。'
         '\nproposed_character_changes 和 proposed_foreshadow_changes 可以为空数组 []，'
         '但如果包含元素则必须严格包含上述必填字段。'},
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'角色：\n{character_lines}\n'
                f'伏笔：\n{foreshadow_lines}\n'
                f'本章目标：{chapter_goal}\n'
                f'{outline_lines}\n'
                '请基于本章目标与 Outliner 节拍生成章节正文，返回 JSON。'
            ),
        },
    ]


def build_critique_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    chapter: Chapter,
    draft: ChapterDraft,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}, profile={c.public_profile}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}, description={f.description}' for f in foreshadows)
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 Critic Agent。必须只返回合法 JSON，结构为：'
                '{"score":0到100,"issues":[{"category":"character_voice|foreshadow|world_rule|pacing|prose",'
                '"severity":"low|medium|high","message":"问题说明"}],'
                '"suggestions":["建议"],"consistency_check":{"character_voice":"...","foreshadow_usage":"...",'
                '"world_rule_adherence":"...","pacing":"..."}}。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'角色：\n{character_lines}\n'
                f'伏笔：\n{foreshadow_lines}\n'
                f'Outliner上下文：{chapter.outline_context}\n'
                f'Outliner节拍：{chapter.outline_beats}\n'
                f'正文：\n{draft.content}\n'
                '请检查角色声音一致性、伏笔使用、世界规则遵守、节奏与语言问题。'
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


def create_chapter_session(db: Session, user: User, world_id: int, chapter_goal: str, title: str | None = None) -> Chapter:
    world = require_owned_world(db, user, world_id)
    characters, _ = _load_world_context(db, world)
    chapter = Chapter(
        world_id=world.id,
        title=title or chapter_goal[:80],
        pov_character_id=characters[0].id if characters else None,
        status='drafting',
        draft_version=1,
        base_world_version=world.world_version,
        chapter_goal=chapter_goal,
        outline_beats=[],
        outline_context={},
        critique_report={},
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def generate_chapter_outline(
    db: Session,
    user: User,
    chapter_id: int,
    chapter_context: str | None = None,
    llm_client: LLMClient | None = None,
) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    if chapter.status == 'approved':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='ALREADY_APPROVED')
    world = db.get(World, chapter.world_id)
    assert world is not None
    characters, foreshadows = _load_world_context(db, world)
    client = _model_client(llm_client)
    try:
        outline = client.generate_outline(
            build_outline_messages(world, characters, foreshadows, chapter.chapter_goal or chapter.title, chapter_context)
        )
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    chapter.outline_beats = [beat.model_dump() for beat in outline.beats]
    chapter.outline_context = _outline_context_payload(outline)
    chapter.status = 'outlined'
    db.commit()
    db.refresh(chapter)
    return {
        'chapter_id': chapter.id,
        'outline_beats': chapter.outline_beats,
        'outline_context': chapter.outline_context,
        'status': chapter.status,
    }


def create_chapter_draft(
    db: Session,
    user: User,
    world_id: int,
    chapter_goal: str,
    llm_client: LLMClient | None = None,
) -> dict:
    world = require_owned_world(db, user, world_id)
    characters, foreshadows = _load_world_context(db, world)
    client = _model_client(llm_client)
    try:
        generation = client.generate_chapter(build_generation_messages(world, characters, foreshadows, chapter_goal))
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    validate_generation_ids(generation, characters, foreshadows)

    chapter = Chapter(
        world_id=world.id,
        title=generation.title,
        pov_character_id=characters[0].id if characters else None,
        status='reviewing',
        draft_version=1,
        base_world_version=world.world_version,
        chapter_goal=chapter_goal,
        outline_beats=[],
        outline_context={},
        critique_report={},
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
    return _draft_payload(chapter, draft)


def write_chapter_from_outline(
    db: Session,
    user: User,
    chapter_id: int,
    outline_beats: list[BeatCard] | None = None,
    llm_client: LLMClient | None = None,
) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    if chapter.status == 'approved':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='ALREADY_APPROVED')
    if outline_beats is not None:
        chapter.outline_beats = [beat.model_dump() for beat in outline_beats]
    if not chapter.outline_beats:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='OUTLINE_REQUIRED')
    world = db.get(World, chapter.world_id)
    assert world is not None
    characters, foreshadows = _load_world_context(db, world)
    client = _model_client(llm_client)
    try:
        generation = client.generate_chapter(
            build_generation_messages(
                world,
                characters,
                foreshadows,
                chapter.chapter_goal or chapter.title,
                chapter.outline_beats,
                chapter.outline_context,
            )
        )
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    validate_generation_ids(generation, characters, foreshadows)

    chapter.title = generation.title
    chapter.status = 'reviewing'
    proposed_changes = {
        'characters': [change.model_dump(exclude_none=True) for change in generation.proposed_character_changes],
        'foreshadows': [change.model_dump(exclude_none=True) for change in generation.proposed_foreshadow_changes],
    }
    draft = _latest_draft(db, chapter)
    if draft is None:
        draft = ChapterDraft(chapter_id=chapter.id, draft_version=chapter.draft_version, content='', context_summary='', source_world_version=world.world_version)
        db.add(draft)
    draft.content = generation.draft_content
    draft.context_summary = generation.context_summary
    draft.review_hints = generation.review_hints
    draft.proposed_changes = proposed_changes
    draft.source_world_version = world.world_version
    draft.rejection_feedback = None
    db.commit()
    db.refresh(chapter)
    db.refresh(draft)
    return _draft_payload(chapter, draft)


def critique_chapter(db: Session, user: User, chapter_id: int, llm_client: LLMClient | None = None) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    draft = _latest_draft(db, chapter)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='DRAFT_REQUIRED')
    world = db.get(World, chapter.world_id)
    assert world is not None
    characters, foreshadows = _load_world_context(db, world)
    client = _model_client(llm_client)
    try:
        report = client.critique_chapter(build_critique_messages(world, characters, foreshadows, chapter, draft))
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    chapter.critique_report = report.model_dump()
    db.commit()
    db.refresh(chapter)
    return {'chapter_id': chapter.id, 'critique_report': chapter.critique_report, 'status': chapter.status}


def reject_chapter(db: Session, user: User, chapter_id: int, feedback: str) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    draft = _latest_draft(db, chapter)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    chapter.status = 'rejected'
    draft.rejection_feedback = feedback
    db.commit()
    db.refresh(chapter)
    db.refresh(draft)
    return _draft_payload(chapter, draft)


def edit_chapter_draft(db: Session, user: User, chapter_id: int, new_content: str) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    if chapter.status == 'approved':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='ALREADY_APPROVED')
    draft = _latest_draft(db, chapter)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    draft.content = new_content
    db.commit()
    db.refresh(chapter)
    db.refresh(draft)
    return _draft_payload(chapter, draft)


def approve_chapter(db: Session, user: User, chapter_id: int) -> Chapter:
    try:
        chapter = db.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
        world = db.scalar(select(World).where(World.id == chapter.world_id).with_for_update())
        if world is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
        if world.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
        draft = _latest_draft(db, chapter)
        if draft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
        if draft.source_world_version != world.world_version:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_VERSION_MISMATCH')

        character_changes = []
        for change in draft.proposed_changes.get('characters', []):
            character = db.get(Character, change.get('character_id'))
            if character is None or character.world_id != world.id:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
            before = character_projection(character)
            after = before | {
                key: change[key]
                for key in ('status', 'current_goals')
                if key in change
            }
            character_changes.append((character, change, before, after))

        foreshadow_changes = []
        for change in draft.proposed_changes.get('foreshadows', []):
            foreshadow = db.get(Foreshadow, change.get('foreshadow_id'))
            if foreshadow is None or foreshadow.world_id != world.id or 'status' not in change:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
            before = foreshadow_projection(foreshadow)
            after = before | {'status': change['status']}
            if change.get('description_note'):
                after['description'] = f"{foreshadow.description}\n审核备注：{change['description_note']}"
            foreshadow_changes.append((foreshadow, change, before, after))

        version_before = world.world_version
        version_after = version_before + 1
        commit_group_id = f'chapter-{chapter.id}-{uuid4().hex}'
        chapter.status = 'approved'
        chapter.approved_content = draft.content
        chapter.approved_version = draft.draft_version

        for character, change, _before, _after in character_changes:
            if 'status' in change:
                character.status = change['status']
            if 'current_goals' in change:
                character.current_goals = change['current_goals']

        for foreshadow, change, _before, _after in foreshadow_changes:
            apply_foreshadow_status_transition(
                db,
                foreshadow,
                change['status'],
                chapter_id=chapter.id,
                note=change.get('description_note'),
            )
            if change.get('description_note'):
                foreshadow.description = f"{foreshadow.description}\n审核备注：{change['description_note']}"

        world.world_version = version_after
        db.flush()
        refresh_world_projection(db, world)

        for character, change, before, after in character_changes:
            db.add(
                EventLog(
                    world_id=world.id,
                    chapter_id=chapter.id,
                    event_type='character_change',
                    source_type='chapter_approval',
                    commit_id=f'{commit_group_id}-character-{character.id}',
                    payload={
                        'commit_group_id': commit_group_id,
                        'chapter_id': chapter.id,
                        'object_type': 'character',
                        'object_id': character.id,
                        'change': change,
                        'before': before,
                        'after': after,
                    },
                    world_version_before=version_before,
                    world_version_after=version_after,
                )
            )

        for foreshadow, change, before, after in foreshadow_changes:
            db.add(
                EventLog(
                    world_id=world.id,
                    chapter_id=chapter.id,
                    event_type='foreshadow_change',
                    source_type='chapter_approval',
                    commit_id=f'{commit_group_id}-foreshadow-{foreshadow.id}',
                    payload={
                        'commit_group_id': commit_group_id,
                        'chapter_id': chapter.id,
                        'object_type': 'foreshadow',
                        'object_id': foreshadow.id,
                        'change': change,
                        'before': before,
                        'after': after,
                    },
                    world_version_before=version_before,
                    world_version_after=version_after,
                )
            )

        db.add(
            EventLog(
                world_id=world.id,
                chapter_id=chapter.id,
                event_type='world_version_increment',
                source_type='chapter_approval',
                commit_id=f'{commit_group_id}-version',
                payload={
                    'commit_group_id': commit_group_id,
                    'chapter_id': chapter.id,
                    'world_version_before': version_before,
                    'world_version_after': version_after,
                },
                world_version_before=version_before,
                world_version_after=version_after,
            )
        )
        db.add(
            EventLog(
                world_id=world.id,
                chapter_id=chapter.id,
                event_type='chapter_approved',
                source_type='chapter_approval',
                commit_id=f'{commit_group_id}-approved',
                payload={
                    'commit_group_id': commit_group_id,
                    'chapter_id': chapter.id,
                    'chapter_title': chapter.title,
                    'approved_version': draft.draft_version,
                    'proposed_changes': draft.proposed_changes,
                },
                world_version_before=version_before,
                world_version_after=version_after,
            )
        )
        db.commit()
        db.refresh(chapter)
        return chapter
    except Exception:
        db.rollback()
        raise
