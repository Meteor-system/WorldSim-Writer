from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.world.models import World
from app.world.templates import SAMPLE_WORLD


def create_sample_world(db: Session, user: User) -> World:
    world = World(
        owner_id=user.id,
        title=SAMPLE_WORLD['title'],
        genre_template=SAMPLE_WORLD['genre_template'],
        truth_canon=SAMPLE_WORLD['truth_canon'],
        truth_canon_version=1,
        world_version=1,
        status='active',
        tone_profile=SAMPLE_WORLD['tone_profile'],
    )
    db.add(world)
    db.flush()

    characters: list[Character] = []
    for item in SAMPLE_WORLD['characters']:
        character = Character(world_id=world.id, **item)
        db.add(character)
        characters.append(character)
    db.flush()

    for item in SAMPLE_WORLD['relations']:
        db.add(
            CharacterRelation(
                world_id=world.id,
                source_character_id=characters[item['source_index']].id,
                target_character_id=characters[item['target_index']].id,
                relation_type=item['relation_type'],
                intensity=item['intensity'],
                visibility=item['visibility'],
            )
        )

    for item in SAMPLE_WORLD['foreshadows']:
        db.add(
            Foreshadow(
                world_id=world.id,
                title=item['title'],
                description=item['description'],
                foreshadow_type=item['foreshadow_type'],
                status=item['status'],
                urgency_level=item['urgency_level'],
                related_character_ids=[characters[index].id for index in item['related_character_indexes']],
                expected_resolution_window=item['expected_resolution_window'],
            )
        )

    db.commit()
    db.refresh(world)
    return world


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
        'characters': characters,
        'relations': relations,
        'foreshadows': foreshadows,
        'recent_events': recent_events,
    }
