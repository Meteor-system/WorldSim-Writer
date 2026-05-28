from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.character.schemas import CharacterCreate, CharacterResponse, CharacterUpdate
from app.character.service import (
    create_character,
    delete_character,
    get_character,
    get_characters,
    update_character,
)
from app.core.database import get_db

router = APIRouter(tags=['characters'])


@router.post('/worlds/{world_id}/characters', response_model=CharacterResponse)
def create(
    world_id: int,
    data: CharacterCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterResponse:
    return CharacterResponse.model_validate(create_character(db, current_user, world_id, data))


@router.get('/worlds/{world_id}/characters', response_model=list[CharacterResponse])
def list_characters(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[CharacterResponse]:
    return [
        CharacterResponse.model_validate(c)
        for c in get_characters(db, current_user, world_id)
    ]


@router.get('/characters/{character_id}', response_model=CharacterResponse)
def get_one(
    character_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterResponse:
    return CharacterResponse.model_validate(get_character(db, current_user, character_id))


@router.put('/characters/{character_id}', response_model=CharacterResponse)
def update(
    character_id: int,
    data: CharacterUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterResponse:
    return CharacterResponse.model_validate(update_character(db, current_user, character_id, data))


@router.delete('/characters/{character_id}', status_code=204)
def delete(
    character_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> None:
    delete_character(db, current_user, character_id)
