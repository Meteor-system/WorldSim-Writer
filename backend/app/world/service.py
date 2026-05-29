from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.world.models import World
from app.world.schemas import WorldCreateRequest
from app.world.templates import SAMPLE_WORLD


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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='INVALID_CHARACTER_INDEX')


def _validate_starter_asset_indexes(data: WorldCreateRequest) -> None:
    character_count = len(data.starter_assets.characters)
    for relation in data.starter_assets.relations:
        _validate_character_index(relation.source_index, character_count)
        _validate_character_index(relation.target_index, character_count)
    for foreshadow in data.starter_assets.foreshadows:
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


def refresh_world_projection(db: Session, world: World) -> None:
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
    world.current_characters = [character_projection(character) for character in characters]
    world.current_foreshadows = [foreshadow_projection(foreshadow) for foreshadow in foreshadows]


def create_world_from_template(db: Session, user: User, data: WorldCreateRequest) -> World:
    _validate_starter_asset_indexes(data)

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

    for item in data.starter_assets.foreshadows:
        db.add(
            Foreshadow(
                world_id=world.id,
                title=item.title,
                description=item.description,
                foreshadow_type=item.foreshadow_type,
                status=item.status if item.status is not None else 'planted',
                urgency_level=item.urgency_level if item.urgency_level is not None else 1,
                related_character_ids=[characters[index].id for index in item.related_character_indexes or []],
                expected_resolution_window=item.expected_resolution_window,
            )
        )
    db.flush()
    refresh_world_projection(db, world)

    db.commit()
    db.refresh(world)
    return world


def create_sample_world(db: Session, user: User) -> World:
    return create_world_from_template(db, user, _sample_world_request())


def list_user_worlds(db: Session, user: User) -> list[World]:
    return list(db.scalars(select(World).where(World.owner_id == user.id).order_by(World.id)))


def require_owned_world(db: Session, user: User, world_id: int) -> World:
    world = db.get(World, world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return world


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
        'characters': characters,
        'relations': relations,
        'foreshadows': foreshadows,
        'recent_events': recent_events,
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
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}
