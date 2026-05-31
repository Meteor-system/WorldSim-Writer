from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.tags.schemas import (
    ObjectTagAssignRequest,
    ObjectTagResponse,
    TagCreateRequest,
    TagDetailResponse,
    TagListResponse,
    TagResponse,
)
from app.tags.service import assign_tag, create_tag, delete_tag, get_tag_detail, list_tags, unassign_tag

router = APIRouter(tags=['tags'])


@router.get('/worlds/{world_id}/tags', response_model=TagListResponse)
def list_world_tags(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagListResponse:
    return TagListResponse.model_validate(list_tags(db, current_user, world_id))


@router.post('/worlds/{world_id}/tags', response_model=TagResponse)
def create_world_tag(
    world_id: int,
    data: TagCreateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    return TagResponse.model_validate(create_tag(db, current_user, world_id, data))


@router.get('/worlds/{world_id}/tags/{tag_id}', response_model=TagDetailResponse)
def get_world_tag(
    world_id: int,
    tag_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagDetailResponse:
    return TagDetailResponse.model_validate(get_tag_detail(db, current_user, world_id, tag_id))


@router.delete('/worlds/{world_id}/tags/{tag_id}', status_code=204)
def delete_world_tag(
    world_id: int,
    tag_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> None:
    delete_tag(db, current_user, world_id, tag_id)


@router.post('/worlds/{world_id}/tags/{tag_id}/objects', response_model=ObjectTagResponse)
def assign_world_tag(
    world_id: int,
    tag_id: int,
    data: ObjectTagAssignRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ObjectTagResponse:
    return ObjectTagResponse.model_validate(assign_tag(db, current_user, world_id, tag_id, data))


@router.delete('/worlds/{world_id}/tags/{tag_id}/objects/{object_type}/{object_id}', status_code=204)
def unassign_world_tag(
    world_id: int,
    tag_id: int,
    object_type: str,
    object_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> None:
    unassign_tag(db, current_user, world_id, tag_id, object_type, object_id)
