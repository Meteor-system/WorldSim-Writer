from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_request_id, require_user
from app.auth.models import User
from app.core.database import get_db
from app.event.schemas import EventLogListResponse
from app.llm.usage import audit_session_factory_from_db
from app.world.schemas import (
    EmptyWorldMutationRequest,
    SerialPlanResponse,
    StoryArcResponse,
    WorldCreateRequest,
    WorldCreationDraftRequest,
    WorldCreationDraftResponse,
    WorldOverviewResponse,
    WorldResponse,
    WorldSearchResponse,
    WorldSeedDetail,
    WorldSeedListResponse,
    WorldStatusUpdateRequest,
)
from app.world.service import (
    create_sample_world,
    create_world_from_seed,
    create_world_from_template,
    generate_world_creation_draft,
    get_world_overview,
    get_world_seed,
    list_user_worlds,
    list_world_events,
    list_world_seeds,
    require_owned_world,
    search_world,
    update_world_status,
)
from app.world.story_arc import generate_story_arc, preview_serial_plan, suggest_chapter_goal

router = APIRouter(prefix='/worlds', tags=['worlds'])


@router.post('', response_model=WorldResponse)
def create_world(
    data: WorldCreateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(create_world_from_template(db, current_user, data))


@router.post('/from-template', response_model=WorldResponse)
def create_from_template(
    _payload: EmptyWorldMutationRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(create_sample_world(db, current_user))


@router.post('/draft-from-brief', response_model=WorldCreationDraftResponse)
def draft_from_brief(
    data: WorldCreationDraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    request_id: str | None = Depends(get_request_id),
) -> WorldCreationDraftResponse:
    style_handbook_reference = (
        data.style_handbook_reference.model_dump() if data.style_handbook_reference else None
    )
    material_references = [reference.model_dump() for reference in data.material_references]
    return WorldCreationDraftResponse.model_validate(
        generate_world_creation_draft(
            data.brief,
            style_handbook_reference=style_handbook_reference,
            variant_count=data.variant_count,
            material_references=material_references,
            db=db,
            audit_session_factory=audit_session_factory_from_db(db),
            request_id=request_id,
        )
    )


@router.get('/seeds', response_model=WorldSeedListResponse)
def seeds(current_user: User = Depends(require_user)) -> WorldSeedListResponse:
    return WorldSeedListResponse.model_validate({'seeds': list_world_seeds()})


@router.get('/seeds/{seed_key}', response_model=WorldSeedDetail)
def seed_detail(seed_key: str, current_user: User = Depends(require_user)) -> WorldSeedDetail:
    return WorldSeedDetail.model_validate(get_world_seed(seed_key))


@router.post('/from-seed/{seed_key}', response_model=WorldResponse)
def create_from_seed(
    seed_key: str,
    _payload: EmptyWorldMutationRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(create_world_from_seed(db, current_user, seed_key))


@router.get('', response_model=list[WorldResponse])
def list_worlds(current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> list[WorldResponse]:
    return [WorldResponse.model_validate(world) for world in list_user_worlds(db, current_user)]


@router.get('/{world_id}', response_model=WorldResponse)
def get_world(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldResponse:
    return WorldResponse.model_validate(require_owned_world(db, current_user, world_id))


@router.patch('/{world_id}/status', response_model=WorldResponse)
def update_status(
    world_id: int,
    data: WorldStatusUpdateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(update_world_status(db, current_user, world_id, data.status))


@router.get('/{world_id}/overview', response_model=WorldOverviewResponse)
def overview(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldOverviewResponse:
    return WorldOverviewResponse.model_validate(get_world_overview(db, current_user, world_id))


@router.post('/{world_id}/story-arc', response_model=StoryArcResponse)
def story_arc(
    world_id: int,
    _payload: EmptyWorldMutationRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    request_id: str | None = Depends(get_request_id),
) -> StoryArcResponse:
    return StoryArcResponse.model_validate(
        generate_story_arc(db, current_user, world_id, request_id=request_id)
    )


@router.get('/{world_id}/serial-plan', response_model=SerialPlanResponse)
def serial_plan(
    world_id: int,
    limit: int = Query(3, ge=1, le=5),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> SerialPlanResponse:
    return SerialPlanResponse.model_validate(preview_serial_plan(db, current_user, world_id, limit))


@router.post('/{world_id}/suggest-goal')
def suggest_goal(
    world_id: int,
    _payload: EmptyWorldMutationRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
    request_id: str | None = Depends(get_request_id),
) -> dict:
    return suggest_chapter_goal(db, current_user, world_id, request_id=request_id)


@router.get('/{world_id}/events', response_model=EventLogListResponse)
def events(
    world_id: int,
    event_type: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> EventLogListResponse:
    return EventLogListResponse.model_validate(list_world_events(db, current_user, world_id, event_type, limit, offset))


@router.get('/{world_id}/search', response_model=WorldSearchResponse)
def search(
    world_id: int,
    q: str,
    object_types: str | None = None,
    tags: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldSearchResponse:
    return WorldSearchResponse.model_validate(search_world(db, current_user, world_id, q, object_types, limit, tags))
