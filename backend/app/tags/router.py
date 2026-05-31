from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.tags.schemas import (
    ObjectTagAssignRequest,
    ObjectTagBulkAssignRequest,
    ObjectTagBulkAssignResponse,
    ObjectTagResponse,
    TagCreateRequest,
    TagDetailResponse,
    TagListResponse,
    TagMergeRequest,
    TagMergeResponse,
    TagResponse,
    TagUpdateRequest,
)
from app.tags.service import assign_tag, bulk_assign_tag, create_tag, delete_tag, get_tag_detail, list_tags, merge_tag, unassign_tag, update_tag

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


@router.patch('/worlds/{world_id}/tags/{tag_id}', response_model=TagResponse)
def update_world_tag(
    world_id: int,
    tag_id: int,
    data: TagUpdateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    return TagResponse.model_validate(update_tag(db, current_user, world_id, tag_id, data))


@router.post('/worlds/{world_id}/tags/{source_tag_id}/merge', response_model=TagMergeResponse)
def merge_world_tag(
    world_id: int,
    source_tag_id: int,
    data: TagMergeRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagMergeResponse:
    return TagMergeResponse.model_validate(merge_tag(db, current_user, world_id, source_tag_id, data))


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


@router.post('/worlds/{world_id}/tags/{tag_id}/objects/bulk', response_model=ObjectTagBulkAssignResponse)
def bulk_assign_world_tag(
    world_id: int,
    tag_id: int,
    data: ObjectTagBulkAssignRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ObjectTagBulkAssignResponse:
    return ObjectTagBulkAssignResponse.model_validate(bulk_assign_tag(db, current_user, world_id, tag_id, data))


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
