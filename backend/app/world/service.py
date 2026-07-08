import json
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow, ForeshadowEvent
from app.narrative.models import Chapter
from app.tags.models import ObjectTag, Tag
from app.world.models import World
from app.core.config import get_settings
from app.llm.client import LLMClient
from app.world.schemas import WorldCreateRequest
from app.world.seed_library import WORLD_SEEDS, seed_detail, seed_summary
from app.world.templates import SAMPLE_WORLD

FORESHADOW_STATUSES = {'planted', 'advanced', 'resolved', 'expired'}
SAFE_MODEL_RUNTIME_ERRORS = {'MODEL_REQUEST_FAILED', 'MODEL_AUTH_FAILED', 'MODEL_RATE_LIMITED'}


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
    if isinstance(exc, RuntimeError) and str(exc) in SAFE_MODEL_RUNTIME_ERRORS:
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_REQUEST_FAILED')


def _style_handbook_prompt_block(style_handbook_reference: dict | None) -> str:
    if not style_handbook_reference:
        return ''
    handbook = style_handbook_reference.get('handbook') or {}
    dimension_keys = (
        ('narrative_pacing', '叙事节奏'),
        ('language_density', '语言密度'),
        ('dialogue_ratio', '对白比例'),
        ('scene_progression', '场景推进'),
        ('suspense_structure', '悬念结构'),
        ('relationship_tension', '关系张力'),
        ('foreshadowing_pattern', '伏笔手法'),
    )
    dimension_parts = []
    for key, label in dimension_keys:
        dimension = handbook.get(key) or {}
        value = dimension.get('value')
        if value:
            dimension_parts.append(f'{label}：{value}')
    source_title = style_handbook_reference.get('source_title') or '未命名参考'
    lines = [
        f'用户提供了写作风格手册参考（来源：{source_title}，仅抽象维度，禁止照抄原文、人物名或专有设定）：'
        + '；'.join(dimension_parts),
    ]
    avoid_guidelines = handbook.get('avoid_guidelines') or []
    if avoid_guidelines:
        lines.append('需避免：' + '；'.join(str(g) for g in avoid_guidelines))
    originality_guidelines = handbook.get('originality_guidelines') or []
    if originality_guidelines:
        lines.append('原创性约束：' + '；'.join(str(g) for g in originality_guidelines))
    lines.append('风格手册只影响 tone_profile 的语言气质倾向，不得改变世界事实、角色身份或专有设定，也不写入 canon。')
    return '\n'.join(lines)


def build_world_creation_draft_messages(brief: str, style_handbook_reference: dict | None = None) -> list[dict[str, str]]:
    user_content = (
        f'用户一句话脑洞：{brief}\n'
        '请生成一个可由用户确认和编辑的世界创建草稿。'
        'generation_notes 用 1-3 条说明草稿如何理解用户脑洞；safety_notes 用 1-3 条说明确认前不会写入 canon/正史。'
    )
    style_block = _style_handbook_prompt_block(style_handbook_reference)
    if style_block:
        user_content += '\n' + style_block
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 World Genesis 草稿生成器。必须只返回严格 JSON 对象，不要返回 Markdown、解释或代码块。'
                '任务：把用户一句话故事脑洞扩展成可审阅的世界创建表单草稿，而不是直接创建世界。'
                '返回对象只能包含字段：draft, first_chapter_goal, generation_notes, safety_notes。'
                'draft 必须完全符合 WorldCreateRequest：title, genre_template, truth_canon, tone_profile, starter_assets。'
                'starter_assets.characters 至少 2 个角色；relations 和 foreshadows 使用 source_index/target_index/related_character_indexes 引用角色数组索引。'
                'foreshadow status 只能是 planted、advanced、resolved 或 expired；新世界默认优先 planted。'
                '必须生成原创世界胚胎；如果用户 brief 指向受保护作品、角色名、专有设定或标志性桥段，应抽象为通用题材参数，不复用名称或桥段。'
                '如果提供了写作风格手册参考，只把它当作抽象语言气质倾向，写入 tone_profile 的风格描述，不得复用原文句子、人物名或专有设定。'
                '不得声称已经写入正史、创建世界、推进世界进度或生成正式章节。'
            ),
        },
        {
            'role': 'user',
            'content': user_content,
        },
    ]


def _sample_world_request() -> WorldCreateRequest:
    return WorldCreateRequest.model_validate(
        {
            'title': SAMPLE_WORLD['title'],
            'genre_template': SAMPLE_WORLD['genre_template'],
            'truth_canon': SAMPLE_WORLD['truth_canon'],
            'tone_profile': SAMPLE_WORLD['tone_profile'],
            'starter_assets': {
                'characters': SAMPLE_WORLD['characters'],
                'relations': SAMPLE_WORLD['relations'],
                'foreshadows': SAMPLE_WORLD['foreshadows'],
            },
        }
    )


def _validate_character_index(index: int, character_count: int) -> None:
    if index < 0 or index >= character_count:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='INVALID_CHARACTER_INDEX')


def _validate_starter_assets(data: WorldCreateRequest) -> None:
    character_count = len(data.starter_assets.characters)
    for relation in data.starter_assets.relations:
        _validate_character_index(relation.source_index, character_count)
        _validate_character_index(relation.target_index, character_count)
        if relation.source_index == relation.target_index:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='INVALID_RELATION_SELF_REFERENCE')
    for foreshadow in data.starter_assets.foreshadows:
        foreshadow_status = foreshadow.status if foreshadow.status is not None else 'planted'
        if foreshadow_status not in FORESHADOW_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS')
        for index in foreshadow.related_character_indexes or []:
            _validate_character_index(index, character_count)


def character_projection(character: Character) -> dict:
    return {
        'id': character.id,
        'name': character.name,
        'role_type': character.role_type,
        'status': character.status,
        'public_profile': character.public_profile,
        'hidden_traits': character.hidden_traits,
        'destiny_flag': character.destiny_flag,
        'current_goals': character.current_goals,
    }


def foreshadow_projection(foreshadow: Foreshadow) -> dict:
    return {
        'id': foreshadow.id,
        'title': foreshadow.title,
        'description': foreshadow.description,
        'foreshadow_type': foreshadow.foreshadow_type,
        'status': foreshadow.status,
        'urgency_level': foreshadow.urgency_level,
        'related_character_ids': foreshadow.related_character_ids,
        'expected_resolution_window': foreshadow.expected_resolution_window,
    }


def relation_projection(relation: CharacterRelation) -> dict:
    return {
        'id': relation.id,
        'source_character_id': relation.source_character_id,
        'target_character_id': relation.target_character_id,
        'relation_type': relation.relation_type,
        'intensity': relation.intensity,
        'visibility': relation.visibility,
    }


def refresh_world_projection(db: Session, world: World) -> None:
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
    relations = list(db.scalars(select(CharacterRelation).where(CharacterRelation.world_id == world.id).order_by(CharacterRelation.id)))
    world.current_characters = [character_projection(character) for character in characters]
    world.current_foreshadows = [foreshadow_projection(foreshadow) for foreshadow in foreshadows]
    world.current_relations = [relation_projection(relation) for relation in relations]


def generate_world_creation_draft(
    brief: str,
    llm_client: LLMClient | None = None,
    style_handbook_reference: dict | None = None,
) -> dict:
    client = _model_client(llm_client)
    try:
        generated = client.generate_world_creation_draft(
            build_world_creation_draft_messages(brief, style_handbook_reference)
        )
        draft = WorldCreateRequest.model_validate(generated.draft)
        _validate_starter_assets(draft)
    except HTTPException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID') from exc
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    return {
        'source_brief': brief,
        'draft': draft,
        'first_chapter_goal': generated.first_chapter_goal,
        'generation_notes': generated.generation_notes,
        'safety_notes': generated.safety_notes,
        'style_handbook_reference': style_handbook_reference,
    }


def create_world_from_template(db: Session, user: User, data: WorldCreateRequest) -> World:
    _validate_starter_assets(data)

    world = World(
        owner_id=user.id,
        title=data.title,
        genre_template=data.genre_template,
        truth_canon=data.truth_canon,
        truth_canon_version=1,
        world_version=1,
        status='active',
        tone_profile=data.tone_profile,
    )
    db.add(world)
    db.flush()

    characters: list[Character] = []
    for item in data.starter_assets.characters:
        character = Character(
            world_id=world.id,
            name=item.name,
            role_type=item.role_type,
            status=item.status if item.status is not None else 'active',
            public_profile=item.public_profile if item.public_profile is not None else {},
            hidden_traits=item.hidden_traits if item.hidden_traits is not None else {},
            destiny_flag=item.destiny_flag,
            current_goals=item.current_goals if item.current_goals is not None else [],
        )
        db.add(character)
        characters.append(character)
    db.flush()

    for item in data.starter_assets.relations:
        db.add(
            CharacterRelation(
                world_id=world.id,
                source_character_id=characters[item.source_index].id,
                target_character_id=characters[item.target_index].id,
                relation_type=item.relation_type,
                intensity=item.intensity,
                visibility=item.visibility,
            )
        )

    foreshadows: list[Foreshadow] = []
    for item in data.starter_assets.foreshadows:
        foreshadow_status = item.status if item.status is not None else 'planted'
        if foreshadow_status not in FORESHADOW_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS')
        foreshadow = Foreshadow(
            world_id=world.id,
            title=item.title,
            description=item.description,
            foreshadow_type=item.foreshadow_type,
            status=foreshadow_status,
            urgency_level=item.urgency_level if item.urgency_level is not None else 1,
            related_character_ids=[characters[index].id for index in item.related_character_indexes or []],
            expected_resolution_window=item.expected_resolution_window,
        )
        db.add(foreshadow)
        foreshadows.append(foreshadow)
    db.flush()
    for foreshadow in foreshadows:
        db.add(ForeshadowEvent(foreshadow_id=foreshadow.id, event_type=foreshadow.status))
    refresh_world_projection(db, world)
    db.add(
        EventLog(
            world_id=world.id,
            chapter_id=None,
            event_type='WORLD_CREATED',
            source_type='world_creation',
            commit_id=f'world-{world.id}-created-{uuid4().hex}',
            payload={
                'world_id': world.id,
                'title': world.title,
                'genre_template': world.genre_template,
                'starter_counts': {
                    'characters': len(characters),
                    'relations': len(data.starter_assets.relations),
                    'foreshadows': len(foreshadows),
                },
                'starter_assets': {
                    'character_names': [item.name for item in data.starter_assets.characters],
                    'character_goals': [goal for item in data.starter_assets.characters for goal in item.current_goals or []],
                    'foreshadow_titles': [item.title for item in data.starter_assets.foreshadows],
                    'foreshadow_descriptions': [item.description for item in data.starter_assets.foreshadows],
                },
            },
            world_version_before=0,
            world_version_after=world.world_version,
        )
    )

    db.commit()
    db.refresh(world)
    return world


def create_sample_world(db: Session, user: User) -> World:
    return create_world_from_template(db, user, _sample_world_request())


def _find_world_seed(seed_key: str) -> dict:
    for seed in WORLD_SEEDS:
        if seed['key'] == seed_key:
            return seed
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='SEED_NOT_FOUND')


def list_world_seeds() -> list[dict]:
    return [seed_summary(seed) for seed in WORLD_SEEDS]


def get_world_seed(seed_key: str) -> dict:
    return seed_detail(_find_world_seed(seed_key))


def create_world_from_seed(db: Session, user: User, seed_key: str) -> World:
    seed = _find_world_seed(seed_key)
    data = WorldCreateRequest.model_validate(seed['payload'])
    return create_world_from_template(db, user, data)


def list_user_worlds(db: Session, user: User) -> list[World]:
    return list(db.scalars(select(World).where(World.owner_id == user.id).order_by(World.id)))


def update_world_status(db: Session, user: User, world_id: int, next_status: str) -> World:
    world = require_owned_world(db, user, world_id)
    previous_status = world.status
    world.status = next_status
    if previous_status != next_status:
        db.add(
            EventLog(
                world_id=world.id,
                chapter_id=None,
                event_type='world_status_changed',
                source_type='world_status',
                commit_id=f'world-status-{world.id}-{uuid4().hex}',
                payload={'previous_status': previous_status, 'next_status': next_status},
                world_version_before=world.world_version,
                world_version_after=world.world_version,
            )
        )
    db.commit()
    db.refresh(world)
    return world


def require_owned_world(db: Session, user: User, world_id: int) -> World:
    world = db.get(World, world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return world


def count_approved_chapters(db: Session, world_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id).where(Chapter.status == 'approved')
    ) or 0


def get_world_overview(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    relations = list(db.scalars(select(CharacterRelation).where(CharacterRelation.world_id == world.id).order_by(CharacterRelation.id)))
    foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
    recent_events = list(db.scalars(select(EventLog).where(EventLog.world_id == world.id).order_by(desc(EventLog.id)).limit(10)))
    return {
        'id': world.id,
        'title': world.title,
        'genre_template': world.genre_template,
        'truth_canon': world.truth_canon,
        'truth_canon_version': world.truth_canon_version,
        'world_version': world.world_version,
        'status': world.status,
        'tone_profile': world.tone_profile,
        'current_characters': world.current_characters,
        'current_foreshadows': world.current_foreshadows,
        'current_relations': world.current_relations,
        'characters': characters,
        'relations': relations,
        'foreshadows': foreshadows,
        'recent_events': recent_events,
        'story_arc': world.story_arc,
        'approved_chapter_count': count_approved_chapters(db, world.id),
    }


def list_world_events(db: Session, user: User, world_id: int, event_type: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    world = require_owned_world(db, user, world_id)
    query = select(EventLog).where(EventLog.world_id == world.id)
    count_query = select(func.count()).select_from(EventLog).where(EventLog.world_id == world.id)
    if event_type is not None:
        query = query.where(EventLog.event_type == event_type)
        count_query = count_query.where(EventLog.event_type == event_type)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.order_by(desc(EventLog.id)).limit(limit).offset(offset)))
    type_rows = db.execute(
        select(EventLog.event_type, func.count()).where(EventLog.world_id == world.id).group_by(EventLog.event_type)
    ).all()
    latest_world_version = db.scalar(select(func.max(EventLog.world_version_after)).where(EventLog.world_id == world.id)) or world.world_version
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset,
        'summary': {
            'total': sum(count for _, count in type_rows),
            'event_type_counts': {event_type: count for event_type, count in type_rows},
            'latest_world_version': latest_world_version,
        },
    }


SEARCH_OBJECT_TYPES = {'world', 'character', 'foreshadow', 'chapter', 'event'}


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _matches(text: str, needle: str) -> bool:
    return needle in text.lower()


def _snippet(text: str, query: str, size: int = 140) -> str:
    compact = ' '.join(text.split())
    index = compact.lower().find(query.lower())
    if index == -1:
        return compact[:size]
    start = max(0, index - 40)
    end = min(len(compact), index + len(query) + 100)
    prefix = '…' if start > 0 else ''
    suffix = '…' if end < len(compact) else ''
    return f'{prefix}{compact[start:end]}{suffix}'


def _parse_object_types(object_types: str | None) -> set[str]:
    if object_types is None or object_types.strip() == '':
        return set(SEARCH_OBJECT_TYPES)
    requested = {item.strip() for item in object_types.split(',') if item.strip()}
    return requested & SEARCH_OBJECT_TYPES


def _parse_tag_filters(tags: str | None) -> set[str]:
    if tags is None or tags.strip() == '':
        return set()
    return {item.strip() for item in tags.split(',') if item.strip()}


def _tag_metadata(tag: Tag) -> dict:
    return {'id': tag.id, 'name': tag.name, 'slug': tag.slug, 'color': tag.color}


def _load_tag_filter_assignments(db: Session, world_id: int, tag_filters: set[str]) -> tuple[set[tuple[str, int]], dict[tuple[str, int], list[dict]]] | None:
    if not tag_filters:
        return None

    numeric_ids = {int(value) for value in tag_filters if value.isdigit()}
    text_filters = {value.lower() for value in tag_filters if not value.isdigit()}
    conditions = []
    if numeric_ids:
        conditions.append(Tag.id.in_(numeric_ids))
    if text_filters:
        conditions.append(func.lower(Tag.slug).in_(text_filters))
        conditions.append(func.lower(Tag.name).in_(text_filters))
    if not conditions:
        return set(), {}

    matched_tags = list(db.scalars(select(Tag).where(Tag.world_id == world_id).where(or_(*conditions)).order_by(Tag.id)))
    if not matched_tags:
        return set(), {}

    tag_by_id = {tag.id: tag for tag in matched_tags}
    assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.tag_id.in_(tag_by_id)).order_by(ObjectTag.id)))
    allowed_objects: set[tuple[str, int]] = set()
    metadata_by_object: dict[tuple[str, int], list[dict]] = {}
    for assignment in assignments:
        key = (assignment.object_type, assignment.object_id)
        allowed_objects.add(key)
        metadata_by_object.setdefault(key, []).append(_tag_metadata(tag_by_id[assignment.tag_id]))
    return allowed_objects, metadata_by_object


def _load_object_tag_metadata(db: Session, world_id: int) -> dict[tuple[str, int], list[dict]]:
    assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.world_id == world_id).order_by(ObjectTag.id)))
    if not assignments:
        return {}

    tag_ids = {assignment.tag_id for assignment in assignments}
    tags = list(db.scalars(select(Tag).where(Tag.world_id == world_id).where(Tag.id.in_(tag_ids)).order_by(Tag.id)))
    tag_by_id = {tag.id: tag for tag in tags}
    metadata_by_object: dict[tuple[str, int], list[dict]] = {}
    for assignment in assignments:
        tag = tag_by_id.get(assignment.tag_id)
        if tag is None:
            continue
        key = (assignment.object_type, assignment.object_id)
        metadata_by_object.setdefault(key, []).append(_tag_metadata(tag))
    return metadata_by_object


def _append_search_result(
    results: list[dict],
    result: dict,
    tag_filter_data: tuple[set[tuple[str, int]], dict[tuple[str, int], list[dict]]] | None,
    tag_metadata_by_object: dict[tuple[str, int], list[dict]],
) -> None:
    object_id = result.get('object_id')
    key = (result['object_type'], object_id) if object_id is not None else None
    if tag_filter_data is not None:
        allowed_objects, _ = tag_filter_data
        if key is None or key not in allowed_objects:
            return
    if key is not None and key in tag_metadata_by_object:
        result['metadata'] = {**result.get('metadata', {}), 'tags': tag_metadata_by_object[key]}
    results.append(result)


def search_world(db: Session, user: User, world_id: int, query: str, object_types: str | None = None, limit: int = 20, tags: str | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
    normalized_query = query.strip()
    if not normalized_query:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='SEARCH_QUERY_REQUIRED')
    needle = normalized_query.lower()
    allowed_types = _parse_object_types(object_types)
    tag_filter_data = _load_tag_filter_assignments(db, world.id, _parse_tag_filters(tags))
    tag_metadata_by_object = _load_object_tag_metadata(db, world.id)
    results: list[dict] = []

    if 'world' in allowed_types:
        world_text = ' '.join([world.title, world.genre_template, world.truth_canon, _json_text(world.tone_profile)])
        if _matches(world_text, needle):
            _append_search_result(
                results,
                {
                    'object_type': 'world',
                    'object_id': world.id,
                    'title': world.title,
                    'subtitle': f'World · {world.genre_template}',
                    'snippet': _snippet(world_text, normalized_query),
                    'metadata': {'world_version': world.world_version},
                },
                tag_filter_data,
            )

    if 'character' in allowed_types:
        characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
        for character in characters:
            text = ' '.join(
                [
                    character.name,
                    character.role_type,
                    character.status,
                    character.destiny_flag or '',
                    _json_text(character.public_profile),
                    _json_text(character.hidden_traits),
                    _json_text(character.current_goals),
                ]
            )
            if _matches(text, needle):
                _append_search_result(
                    results,
                    {
                        'object_type': 'character',
                        'object_id': character.id,
                        'title': character.name,
                        'subtitle': f'Character · {character.role_type}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': character.status},
                    },
                    tag_filter_data,
                    tag_metadata_by_object,
                )

    if 'foreshadow' in allowed_types:
        foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
        for foreshadow in foreshadows:
            text = ' '.join(
                [
                    foreshadow.title,
                    foreshadow.description,
                    foreshadow.foreshadow_type,
                    foreshadow.status,
                    foreshadow.expected_resolution_window or '',
                    _json_text(foreshadow.related_character_ids),
                ]
            )
            if _matches(text, needle):
                _append_search_result(
                    results,
                    {
                        'object_type': 'foreshadow',
                        'object_id': foreshadow.id,
                        'title': foreshadow.title,
                        'subtitle': f'Foreshadow · {foreshadow.status} · urgency {foreshadow.urgency_level}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': foreshadow.status, 'urgency_level': foreshadow.urgency_level},
                    },
                    tag_filter_data,
                    tag_metadata_by_object,
                )

    if 'chapter' in allowed_types:
        chapters = list(db.scalars(select(Chapter).where(Chapter.world_id == world.id).order_by(Chapter.id)))
        for chapter in chapters:
            text = ' '.join([chapter.title, chapter.chapter_goal or '', chapter.approved_content or ''])
            if _matches(text, needle):
                _append_search_result(
                    results,
                    {
                        'object_type': 'chapter',
                        'object_id': chapter.id,
                        'title': chapter.title,
                        'subtitle': f'Chapter · {chapter.status} · world v{chapter.base_world_version}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': chapter.status, 'draft_version': chapter.draft_version},
                    },
                    tag_filter_data,
                    tag_metadata_by_object,
                )

    if 'event' in allowed_types:
        events = list(db.scalars(select(EventLog).where(EventLog.world_id == world.id).order_by(EventLog.id)))
        for event in events:
            text = ' '.join([event.event_type, event.source_type, _json_text(event.payload)])
            if _matches(text, needle):
                _append_search_result(
                    results,
                    {
                        'object_type': 'event',
                        'object_id': event.id,
                        'title': event.event_type,
                        'subtitle': f'Event · {event.source_type} · world {event.world_version_before} → {event.world_version_after}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'world_version_after': event.world_version_after, 'chapter_id': event.chapter_id},
                    },
                    tag_filter_data,
                    tag_metadata_by_object,
                )

    counts: dict[str, int] = {}
    for result in results:
        counts[result['object_type']] = counts.get(result['object_type'], 0) + 1

    return {
        'world_id': world.id,
        'query': normalized_query,
        'object_type_counts': counts,
        'results': results[:limit],
    }
