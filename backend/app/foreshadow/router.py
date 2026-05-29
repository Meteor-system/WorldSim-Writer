from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.foreshadow.schemas import ForeshadowCreate, ForeshadowEventResponse, ForeshadowResponse, ForeshadowUpdate
from app.foreshadow.service import (
    create_foreshadow,
    delete_foreshadow,
    get_foreshadow,
    get_foreshadow_timeline,
    get_foreshadows,
    update_foreshadow,
)

router = APIRouter(tags=['foreshadows'])


@router.post('/worlds/{world_id}/foreshadows', response_model=ForeshadowResponse)
def create(
    world_id: int,
    data: ForeshadowCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ForeshadowResponse:
    return ForeshadowResponse.model_validate(create_foreshadow(db, current_user, world_id, data))


@router.get('/worlds/{world_id}/foreshadows', response_model=list[ForeshadowResponse])
def list_foreshadows(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[ForeshadowResponse]:
    return [
        ForeshadowResponse.model_validate(f)
        for f in get_foreshadows(db, current_user, world_id)
    ]


@router.get('/foreshadows/{foreshadow_id}/timeline', response_model=list[ForeshadowEventResponse])
def timeline(
    foreshadow_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[ForeshadowEventResponse]:
    return [
        ForeshadowEventResponse.model_validate(item)
        for item in get_foreshadow_timeline(db, current_user, foreshadow_id)
    ]


@router.get('/foreshadows/{foreshadow_id}', response_model=ForeshadowResponse)
def get_one(
    foreshadow_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ForeshadowResponse:
    return ForeshadowResponse.model_validate(get_foreshadow(db, current_user, foreshadow_id))


@router.put('/foreshadows/{foreshadow_id}', response_model=ForeshadowResponse)
def update(
    foreshadow_id: int,
    data: ForeshadowUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ForeshadowResponse:
    return ForeshadowResponse.model_validate(
        update_foreshadow(db, current_user, foreshadow_id, data)
    )


@router.delete('/foreshadows/{foreshadow_id}', status_code=204)
def delete(
    foreshadow_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> None:
    delete_foreshadow(db, current_user, foreshadow_id)
