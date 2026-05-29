from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.character.relation_service import (
    create_relation,
    delete_relation,
    get_relation,
    get_relations,
    update_relation,
)
from app.character.schemas import CharacterRelationCreate, CharacterRelationResponse, CharacterRelationUpdate
from app.core.database import get_db

router = APIRouter(tags=['relations'])


@router.post('/worlds/{world_id}/relations', response_model=CharacterRelationResponse)
def create(
    world_id: int,
    data: CharacterRelationCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterRelationResponse:
    return CharacterRelationResponse.model_validate(create_relation(db, current_user, world_id, data))


@router.get('/worlds/{world_id}/relations', response_model=list[CharacterRelationResponse])
def list_relations(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[CharacterRelationResponse]:
    return [
        CharacterRelationResponse.model_validate(relation)
        for relation in get_relations(db, current_user, world_id)
    ]


@router.get('/relations/{relation_id}', response_model=CharacterRelationResponse)
def get_one(
    relation_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterRelationResponse:
    return CharacterRelationResponse.model_validate(get_relation(db, current_user, relation_id))


@router.put('/relations/{relation_id}', response_model=CharacterRelationResponse)
def update(
    relation_id: int,
    data: CharacterRelationUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> CharacterRelationResponse:
    return CharacterRelationResponse.model_validate(update_relation(db, current_user, relation_id, data))


@router.delete('/relations/{relation_id}', status_code=204)
def delete(
    relation_id: int,
    edit_reason: str | None = Query(default=None),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> None:
    delete_relation(db, current_user, relation_id, edit_reason)
