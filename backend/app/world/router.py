from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.world.schemas import WorldCreateRequest, WorldOverviewResponse, WorldResponse
from app.world.service import create_sample_world, create_world_from_template, get_world_overview, list_user_worlds, require_owned_world

router = APIRouter(prefix='/worlds', tags=['worlds'])


@router.post('', response_model=WorldResponse)
def create_world(
    data: WorldCreateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(create_world_from_template(db, current_user, data))


@router.post('/from-template', response_model=WorldResponse)
def create_from_template(current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldResponse:
    return WorldResponse.model_validate(create_sample_world(db, current_user))


@router.get('', response_model=list[WorldResponse])
def list_worlds(current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> list[WorldResponse]:
    return [WorldResponse.model_validate(world) for world in list_user_worlds(db, current_user)]


@router.get('/{world_id}', response_model=WorldResponse)
def get_world(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldResponse:
    return WorldResponse.model_validate(require_owned_world(db, current_user, world_id))


@router.get('/{world_id}/overview', response_model=WorldOverviewResponse)
def overview(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldOverviewResponse:
    return WorldOverviewResponse.model_validate(get_world_overview(db, current_user, world_id))
