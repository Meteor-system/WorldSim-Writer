from datetime import datetime

from pydantic import BaseModel


class EventLogResponse(BaseModel):
    id: int
    event_type: str
    source_type: str
    commit_id: str
    payload: dict
    world_version_before: int
    world_version_after: int
    created_at: datetime

    model_config = {'from_attributes': True}
